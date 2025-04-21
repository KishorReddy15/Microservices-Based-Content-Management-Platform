# Microservices Integration Guide

This guide explains how to integrate our Content Management Platform with another team's microservices.

## Architecture Overview

Our integration architecture consists of:

1. **Integration Layer**: A dedicated service that handles cross-platform communication
2. **Shared Models**: Common data models for consistent data exchange
3. **API Gateway**: Enhanced to route requests to both internal and external services
4. **Monitoring & Observability**: Distributed tracing and metrics collection

## Setup Instructions

### 1. Configure External Service URLs

Create a `.env` file in the project root with the following variables:

```
EXTERNAL_API_GATEWAY_URL=http://external-team-api-gateway:9000
INTEGRATION_SECRET_KEY=your-secure-secret-key
```

Replace the URL with the actual URL of the external team's API gateway.

### 2. Build Shared Models

```bash
cd shared-models
pip install -e .
cd ..
```

### 3. Start the Integrated Platform

```bash
docker-compose -f docker-compose.integration.yml up -d
```

### 4. Verify Integration

Access the integration layer's health endpoint:

```bash
curl http://localhost:8080/health
```

You should see a response indicating the health of both your platform and the external platform.

## Integration Points

### 1. Direct Service Access

The integration layer provides direct routes to external services:

- External User Service: `/external/users`
- External Notification Service: `/external/notifications`
- External Payment Service: `/external/payments`
- External Analytics Service: `/external/analytics`

Example:
```bash
# Get users from external service
curl http://localhost:8080/external/users

# Send notification via external service
curl -X POST http://localhost:8080/external/notifications \
  -H "Content-Type: application/json" \
  -d '{"recipient_id": "user123", "type": "email", "subject": "New Assignment", "message": "You have a new assignment"}'
```

### 2. Generic Service Proxy

For more flexibility, use the generic proxy endpoint:

```bash
# Access any service through the proxy
curl -X POST http://localhost:8080/proxy \
  -H "Content-Type: application/json" \
  -d '{
    "service": "external_user",
    "endpoint": "users/search",
    "method": "POST",
    "data": {"query": "john"}
  }'
```

### 3. Integrated Endpoints

The integration layer provides combined endpoints that aggregate data from multiple services:

```bash
# Get comprehensive user dashboard
curl http://localhost:8080/integrated/user/user123/dashboard
```

## Authentication

For secure cross-service communication, use service tokens:

```bash
# Generate a service token
curl -X POST http://localhost:8080/token/service?service_name=your_service_name

# Use the token in subsequent requests
curl -X POST http://localhost:8080/proxy \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "service": "external_user",
    "endpoint": "users/protected",
    "method": "GET"
  }'
```

## Monitoring

The integrated platform includes:

1. **Jaeger UI**: http://localhost:16686 - For distributed tracing
2. **Prometheus**: http://localhost:9090 - For metrics collection
3. **Grafana**: http://localhost:3000 - For dashboards and visualization

## Network Configuration

When connecting to another team's network:

1. Uncomment the `external: true` line in the `external-network` section of `docker-compose.integration.yml`
2. Set the network name to match the external team's network name

## Troubleshooting

### Common Issues

1. **Connection Refused**:
   - Ensure the external services are running and accessible
   - Check network configuration and firewall settings

2. **Authentication Errors**:
   - Verify that the correct authentication tokens are being used
   - Check token expiration

3. **Data Format Issues**:
   - Use the shared models to ensure consistent data formats
   - Check API documentation for required fields

### Logs

To view logs from the integration layer:

```bash
docker-compose -f docker-compose.integration.yml logs integration-layer
```

## Adding New External Services

To integrate with a new external service:

1. Add the service URL to the `SERVICE_REGISTRY` in `integration-layer/main.py`
2. Create appropriate models in `shared-models/shared_models/models.py`
3. Add endpoints in the integration layer to access the new service
4. Update documentation and tests

## Security Considerations

1. Always use HTTPS in production
2. Implement proper authentication and authorization
3. Validate all input data
4. Use secure secrets management
5. Regularly update dependencies
