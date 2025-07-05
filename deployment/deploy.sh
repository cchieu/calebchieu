#!/bin/bash

# Bible Video Generator Deployment Script
# This script deploys the backend to AWS ECS

set -e

# Configuration
AWS_REGION="us-east-1"
ECR_REPOSITORY="bible-video-backend"
ECS_CLUSTER="bible-video-cluster"
ECS_SERVICE="bible-video-service"
TASK_DEFINITION="bible-video-generator"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting deployment process...${NC}"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install it first.${NC}"
    exit 1
fi

# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}"

echo -e "${YELLOW}📦 Building Docker image...${NC}"

# Build Docker image
cd backend
docker build -t ${ECR_REPOSITORY}:latest .

echo -e "${YELLOW}🏷️  Tagging Docker image...${NC}"

# Tag image for ECR
docker tag ${ECR_REPOSITORY}:latest ${ECR_URI}:latest

echo -e "${YELLOW}🔐 Logging in to ECR...${NC}"

# Login to ECR
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_URI}

echo -e "${YELLOW}📤 Pushing Docker image to ECR...${NC}"

# Push image to ECR
docker push ${ECR_URI}:latest

echo -e "${YELLOW}📋 Updating ECS task definition...${NC}"

# Update task definition with new image
TASK_DEFINITION_JSON=$(cat ../deployment/ecs-task-definition.json)
UPDATED_TASK_DEFINITION=$(echo $TASK_DEFINITION_JSON | sed "s|ACCOUNT_ID|${AWS_ACCOUNT_ID}|g" | sed "s|REGION|${AWS_REGION}|g")

# Register new task definition
NEW_TASK_DEFINITION_ARN=$(aws ecs register-task-definition \
    --cli-input-json "$UPDATED_TASK_DEFINITION" \
    --region ${AWS_REGION} \
    --query 'taskDefinition.taskDefinitionArn' \
    --output text)

echo -e "${YELLOW}🔄 Updating ECS service...${NC}"

# Update ECS service with new task definition
aws ecs update-service \
    --cluster ${ECS_CLUSTER} \
    --service ${ECS_SERVICE} \
    --task-definition ${NEW_TASK_DEFINITION_ARN} \
    --region ${AWS_REGION}

echo -e "${YELLOW}⏳ Waiting for deployment to complete...${NC}"

# Wait for deployment to complete
aws ecs wait services-stable \
    --cluster ${ECS_CLUSTER} \
    --services ${ECS_SERVICE} \
    --region ${AWS_REGION}

echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo -e "${GREEN}🎉 Your Bible Video Generator backend is now live!${NC}"

# Get service endpoint
SERVICE_ENDPOINT=$(aws ecs describe-services \
    --cluster ${ECS_CLUSTER} \
    --services ${ECS_SERVICE} \
    --region ${AWS_REGION} \
    --query 'services[0].loadBalancers[0].loadBalancerName' \
    --output text 2>/dev/null || echo "Not available")

if [ "$SERVICE_ENDPOINT" != "Not available" ]; then
    echo -e "${GREEN}🌐 Service endpoint: ${SERVICE_ENDPOINT}${NC}"
fi

cd ..