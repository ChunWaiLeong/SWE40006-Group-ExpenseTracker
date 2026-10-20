#!/usr/bin/env bash
set -Eeuo pipefail

REGION="ap-southeast-2"
ACCOUNT_ID="744376312898"
REPOSITORY="swe40006-expensetracker"
PROJECT_DIR="/home/ec2-user/SWE40006-Group-ExpenseTracker"
PROJECT_NAME="swe40006-group-expensetracker"

IMAGE_TAG="${1:?Usage: deploy.sh IMAGE_TAG}"
REGISTRY="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"
export ECR_IMAGE="${REGISTRY}/${REPOSITORY}:${IMAGE_TAG}"

cd "$PROJECT_DIR"

echo "Deploying image: $ECR_IMAGE"

# Authenticate and download the new image.
aws ecr get-login-password --region "$REGION" |
  docker login --username AWS --password-stdin "$REGISTRY"

docker pull "$ECR_IMAGE"

# Validate Docker Compose configuration.
docker compose -p "$PROJECT_NAME" \
  -f compose.prod.yaml config --quiet

# Run database migrations using the new image.
docker compose -p "$PROJECT_NAME" \
  -f compose.prod.yaml run --rm --no-deps \
  web flask --app app db upgrade

# Deploy the new image.
docker compose -p "$PROJECT_NAME" \
  -f compose.prod.yaml up -d --no-build --no-deps web

# Check application health for up to 60 seconds.
echo "Checking application health..."

for attempt in $(seq 1 12); do
  if curl --fail --silent --show-error \
    http://localhost/health > /dev/null; then
    echo "Deployment successful."
    exit 0
  fi

  echo "Health check attempt $attempt failed."
  sleep 5
done

echo "Deployment failed: application did not become healthy."
exit 1
