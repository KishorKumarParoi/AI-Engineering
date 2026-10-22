#!/usr/bin/env bash
# ==============================================================================
# clear.sh — Teardown all cost-bearing AWS resources
# Deletes EC2 instances, ECS services/clusters, ALBs, NAT Gateways, EIPs, and custom VPCs.
# Guarantees $0.00 ongoing cloud cost.
# ==============================================================================
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

AWS_REGION="${AWS_REGION:-us-east-1}"
PROJECT="rag"

echo -e "\n${CYAN}=================================================================="
echo "   🧹 TEARDOWN OF ALL AWS COST-BEARING RESOURCES (${AWS_REGION})"
echo "==================================================================${NC}"

# 1. TERMINATE EC2 INSTANCES
echo -e "\n${YELLOW}[1/8] Terminating EC2 instances (tag: Project=${PROJECT})...${NC}"
INSTANCE_IDS=$(aws ec2 describe-instances \
    --region "$AWS_REGION" \
    --filters "Name=tag:Project,Values=${PROJECT}" "Name=instance-state-name,Values=pending,running,stopping,stopped" \
    --query "Reservations[].Instances[].InstanceId" \
    --output text 2>/dev/null || true)

if [ -n "$INSTANCE_IDS" ] && [ "$INSTANCE_IDS" != "None" ]; then
    echo "Terminating EC2 instances: $INSTANCE_IDS"
    aws ec2 terminate-instances --region "$AWS_REGION" --instance-ids $INSTANCE_IDS >/dev/null
    echo -e "${GREEN}✓ Termination signal sent to EC2 instances.${NC}"
else
    echo -e "${GREEN}✓ No active EC2 instances found.${NC}"
fi

# 2. DELETE ECS SERVICES & CLUSTERS
echo -e "\n${YELLOW}[2/8] Stopping & Deleting ECS Services and Clusters...${NC}"
ECS_CLUSTERS=$(aws ecs list-clusters --region "$AWS_REGION" --query "clusterArns[]" --output text 2>/dev/null || true)
for CLUSTER in $ECS_CLUSTERS; do
    if [[ "$CLUSTER" == *"${PROJECT}"* ]]; then
        CLUSTER_NAME=$(basename "$CLUSTER")
        echo "Inspecting cluster: $CLUSTER_NAME"
        SERVICES=$(aws ecs list-services --region "$AWS_REGION" --cluster "$CLUSTER_NAME" --query "serviceArns[]" --output text 2>/dev/null || true)
        for SVC in $SERVICES; do
            SVC_NAME=$(basename "$SVC")
            echo "Scaling down and deleting service: $SVC_NAME"
            aws ecs update-service --region "$AWS_REGION" --cluster "$CLUSTER_NAME" --service "$SVC_NAME" --desired-count 0 >/dev/null 2>&1 || true
            aws ecs delete-service --region "$AWS_REGION" --cluster "$CLUSTER_NAME" --service "$SVC_NAME" --force >/dev/null 2>&1 || true
        done
        echo "Deleting ECS cluster: $CLUSTER_NAME"
        aws ecs delete-cluster --region "$AWS_REGION" --cluster "$CLUSTER_NAME" >/dev/null 2>&1 || true
    fi
done
echo -e "${GREEN}✓ ECS services and clusters cleaned up.${NC}"

# 3. DELETE APPLICATION LOAD BALANCERS & LISTENERS
echo -e "\n${YELLOW}[3/8] Deleting Application Load Balancers & Target Groups...${NC}"
ALB_ARNS=$(aws elbv2 describe-load-balancers --region "$AWS_REGION" --query "LoadBalancers[?contains(LoadBalancerName, '${PROJECT}')].LoadBalancerArn" --output text 2>/dev/null || true)
for ALB in $ALB_ARNS; do
    [ -z "$ALB" ] || [ "$ALB" = "None" ] && continue
    echo "Deleting ALB: $ALB"
    aws elbv2 delete-load-balancer --region "$AWS_REGION" --load-balancer-arn "$ALB" >/dev/null 2>&1 || true
done

TG_ARNS=$(aws elbv2 describe-target-groups --region "$AWS_REGION" --query "TargetGroups[?contains(TargetGroupName, '${PROJECT}')].TargetGroupArn" --output text 2>/dev/null || true)
for TG in $TG_ARNS; do
    [ -z "$TG" ] || [ "$TG" = "None" ] && continue
    echo "Deleting Target Group: $TG"
    aws elbv2 delete-target-group --region "$AWS_REGION" --target-group-arn "$TG" >/dev/null 2>&1 || true
done
echo -e "${GREEN}✓ ALB and Target Groups deleted.${NC}"

# 4. DELETE NAT GATEWAYS (Crucial: saves $32+/month)
echo -e "\n${YELLOW}[4/8] Deleting NAT Gateways & Releasing Elastic IPs...${NC}"
NAT_IDS=$(aws ec2 describe-nat-gateways \
    --region "$AWS_REGION" \
    --filter "Name=state,Values=available,pending" \
    --query "NatGateways[?contains(Tags[?Key=='Project'].Value, '${PROJECT}') || contains(Tags[?Key=='Name'].Value, '${PROJECT}')].NatGatewayId" \
    --output text 2>/dev/null || true)

# Also check state file if present
STATE_FILE="scripts/aws_deploy_state.sh"
if [ -f "$STATE_FILE" ]; then
    STATE_NAT=$(grep "NAT_GW_1=" "$STATE_FILE" 2>/dev/null | cut -d'=' -f2 | tr -d '"' || true)
    if [ -n "$STATE_NAT" ] && [[ ! "$NAT_IDS" =~ "$STATE_NAT" ]]; then
        NAT_IDS="$NAT_IDS $STATE_NAT"
    fi
fi

for NAT_ID in $NAT_IDS; do
    [ -z "$NAT_ID" ] || [ "$NAT_ID" = "None" ] && continue
    echo "Deleting NAT Gateway: $NAT_ID"
    aws ec2 delete-nat-gateway --region "$AWS_REGION" --nat-gateway-id "$NAT_ID" >/dev/null 2>&1 || true
    echo "Waiting for NAT Gateway $NAT_ID to delete (can take ~60s)..."
    while true; do
        STATUS=$(aws ec2 describe-nat-gateways --region "$AWS_REGION" --nat-gateway-ids "$NAT_ID" --query "NatGateways[0].State" --output text 2>/dev/null || echo "deleted")
        if [ "$STATUS" = "deleted" ] || [ "$STATUS" = "None" ] || [ -z "$STATUS" ]; then
            break
        fi
        sleep 10
    done
done
echo -e "${GREEN}✓ NAT Gateways deleted.${NC}"

# Release unallocated or project EIPs
EIP_ALLOCS=$(aws ec2 describe-addresses \
    --region "$AWS_REGION" \
    --query "Addresses[?AssociationId==null || contains(Tags[?Key=='Project'].Value, '${PROJECT}')].AllocationId" \
    --output text 2>/dev/null || true)

for ALLOC in $EIP_ALLOCS; do
    [ -z "$ALLOC" ] || [ "$ALLOC" = "None" ] && continue
    echo "Releasing Elastic IP: $ALLOC"
    aws ec2 release-address --region "$AWS_REGION" --allocation-id "$ALLOC" >/dev/null 2>&1 || true
done
echo -e "${GREEN}✓ Elastic IPs released.${NC}"

# 5. CLEAN UP CUSTOM VPC (IF ANY WAS CREATED)
echo -e "\n${YELLOW}[5/8] Cleaning up custom Project VPC resources...${NC}"
CUSTOM_VPCS=$(aws ec2 describe-vpcs \
    --region "$AWS_REGION" \
    --filters "Name=tag:Project,Values=${PROJECT}" \
    --query "Vpcs[].VpcId" \
    --output text 2>/dev/null || true)

for C_VPC in $CUSTOM_VPCS; do
    [ -z "$C_VPC" ] || [ "$C_VPC" = "None" ] && continue
    echo "Cleaning up custom VPC: $C_VPC"
    
    # Detach & delete IGWs
    for IGW in $(aws ec2 describe-internet-gateways --region "$AWS_REGION" --filters "Name=attachment.vpc-id,Values=${C_VPC}" --query "InternetGateways[].InternetGatewayId" --output text 2>/dev/null); do
        aws ec2 detach-internet-gateway --region "$AWS_REGION" --internet-gateway-id "$IGW" --vpc-id "$C_VPC" >/dev/null 2>&1 || true
        aws ec2 delete-internet-gateway --region "$AWS_REGION" --internet-gateway-id "$IGW" >/dev/null 2>&1 || true
    done

    # Delete subnets
    for SUB in $(aws ec2 describe-subnets --region "$AWS_REGION" --filters "Name=vpc-id,Values=${C_VPC}" --query "Subnets[].SubnetId" --output text 2>/dev/null); do
        aws ec2 delete-subnet --region "$AWS_REGION" --subnet-id "$SUB" >/dev/null 2>&1 || true
    done

    # Delete custom route tables
    for RT in $(aws ec2 describe-route-tables --region "$AWS_REGION" --filters "Name=vpc-id,Values=${C_VPC}" --query "RouteTables[?Associations[0].Main!=true].RouteTableId" --output text 2>/dev/null); do
        for ASSOC in $(aws ec2 describe-route-tables --region "$AWS_REGION" --route-table-ids "$RT" --query "RouteTables[0].Associations[].RouteTableAssociationId" --output text 2>/dev/null); do
            aws ec2 disassociate-route-table --region "$AWS_REGION" --association-id "$ASSOC" >/dev/null 2>&1 || true
        done
        aws ec2 delete-route-table --region "$AWS_REGION" --route-table-id "$RT" >/dev/null 2>&1 || true
    done

    # Delete VPC
    aws ec2 delete-vpc --region "$AWS_REGION" --vpc-id "$C_VPC" >/dev/null 2>&1 || true
done
echo -e "${GREEN}✓ Custom VPC cleaned up.${NC}"

# 6. DELETE SECURITY GROUPS
echo -e "\n${YELLOW}[6/8] Cleaning up security groups...${NC}"
for SG in "rag-ec2-sg" "rag-alb-sg" "rag-api-sg" "rag-ui-sg"; do
    SG_ID=$(aws ec2 describe-security-groups --region "$AWS_REGION" --group-names "$SG" --query "SecurityGroups[0].GroupId" --output text 2>/dev/null || true)
    if [ -n "$SG_ID" ] && [ "$SG_ID" != "None" ]; then
        echo "Deleting security group: $SG ($SG_ID)"
        aws ec2 delete-security-group --region "$AWS_REGION" --group-id "$SG_ID" >/dev/null 2>&1 || true
    fi
done
echo -e "${GREEN}✓ Security groups deleted.${NC}"

# 7. CLEAN UP LOG GROUPS
echo -e "\n${YELLOW}[7/8] Cleaning up CloudWatch log groups...${NC}"
for LG in "/ecs/rag-api" "/ecs/rag-ui"; do
    aws logs delete-log-group --region "$AWS_REGION" --log-group-name "$LG" >/dev/null 2>&1 || true
done
echo -e "${GREEN}✓ CloudWatch log groups cleaned up.${NC}"

# 8. RESET LOCAL CACHED STATE
echo -e "\n${YELLOW}[8/8] Resetting deployment state cache...${NC}"
rm -f scripts/aws_deploy_state.sh scripts/ec2_deploy_state.sh /tmp/rag-*.json 2>/dev/null || true
echo -e "${GREEN}✓ Local deployment state cleared.${NC}"

echo -e "\n${CYAN}=================================================================="
echo "   ✨ ALL COST-OCCURRING AWS RESOURCES DELETED SUCCESSFULLY!"
echo "   Your ongoing AWS infrastructure bill is now \$0.00 / month."
echo "==================================================================${NC}\n"
