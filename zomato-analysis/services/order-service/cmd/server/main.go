package main

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/zomato/order-service/internal/events"
	"github.com/zomato/order-service/internal/handler"
	"github.com/zomato/order-service/internal/repository"
	"github.com/zomato/order-service/internal/service"
)

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8081"
	}

	log.Printf("[BOOTSTRAP] Starting Zomato Order Microservice on port %s...", port)

	// Dependency Injection (Clean Hexagonal Architecture)
	repo := repository.NewMemoryOrderRepository()
	eventProducer := events.NewLoggingEventProducer()
	saga := events.NewSagaOrchestrator(eventProducer)
	orderService := service.NewOrderService(repo, saga)
	orderHandler := handler.NewOrderHandler(orderService)

	mux := http.NewServeMux()
	orderHandler.RegisterRoutes(mux)

	server := &http.Server{
		Addr:         fmt.Sprintf(":%s", port),
		Handler:      mux,
		ReadTimeout:  10 * time.Second,
		WriteTimeout: 30 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	// Graceful Shutdown Channel
	stop := make(chan os.Signal, 1)
	signal.Notify(stop, os.Interrupt, syscall.SIGTERM)

	go func() {
		log.Printf("[READY] Order Service listening on http://localhost:%s", port)
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("[FATAL] Server listen failed: %v", err)
		}
	}()

	<-stop
	log.Println("[SHUTDOWN] Signal received. Shutting down gracefully...")

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if err := server.Shutdown(ctx); err != nil {
		log.Fatalf("[ERROR] Server forced to shutdown: %v", err)
	}

	log.Println("[STOPPED] Order Service terminated cleanly.")
}
