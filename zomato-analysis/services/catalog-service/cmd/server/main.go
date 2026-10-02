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

	"github.com/zomato/catalog-service/internal/handler"
	"github.com/zomato/catalog-service/internal/repository"
)

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8082"
	}

	log.Printf("[BOOTSTRAP] Starting Zomato Catalog Microservice on port %s...", port)

	repo := repository.NewMemoryCatalogRepository()
	catalogHandler := handler.NewCatalogHandler(repo)

	mux := http.NewServeMux()
	catalogHandler.RegisterRoutes(mux)

	server := &http.Server{
		Addr:         fmt.Sprintf(":%s", port),
		Handler:      mux,
		ReadTimeout:  10 * time.Second,
		WriteTimeout: 10 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	stop := make(chan os.Signal, 1)
	signal.Notify(stop, os.Interrupt, syscall.SIGTERM)

	go func() {
		log.Printf("[READY] Catalog Service listening on http://localhost:%s", port)
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("[FATAL] Server listen failed: %v", err)
		}
	}()

	<-stop
	log.Println("[SHUTDOWN] Signal received. Shutting down Catalog Service gracefully...")

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if err := server.Shutdown(ctx); err != nil {
		log.Fatalf("[ERROR] Forced shutdown: %v", err)
	}

	log.Println("[STOPPED] Catalog Service terminated cleanly.")
}
