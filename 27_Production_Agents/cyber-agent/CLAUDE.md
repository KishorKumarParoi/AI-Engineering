# Project Context for Claude Code

## Overall context
- This is a project being developed as part of Ed's course "AI in Production"
- Ed is writing this code which thousands of students will clone; they will then follow the steps to deploy
- Students may be on Windows PC, Mac or Linux; the instructions needs to work on all systems
- This project is called Cybersecurity Analyzer - it runs an Agent
- The project will be deployed locally with npm and uv run (working), also locally as a single Docker container (working), to Azure Container App (working), and to GCP Cloud Run (not started)
- The project root is ~/projects/cyber
- There is a .env file in the project root; you may not be able to see it for security reasons, but it's there, with OPENAI_API_KEY and SEMGREP_APP_TOKEN

## Project Overview
Cybersecurity Analyzer - A web application for analyzing Python code for security vulnerabilities using AI-powered analysis with OpenAI and Semgrep.

**Educational Purpose**: This project serves as a teaching tool for students learning cloud deployment on Azure and Google Cloud Platform. Students will gain hands-on experience deploying containerized applications using modern serverless platforms.

## Architecture
- **Frontend**: Next.js (React) with TypeScript, Tailwind CSS
  - Located in `frontend/`
  - Runs on port 3000 in development
  - Built as static export for production
- **Backend**: FastAPI with Python 3.12
  - Located in `backend/`
  - Runs on port 8000
  - Uses OpenAI Agents SDK with Semgrep MCP server

## Key Technical Decisions

### Docker Deployment (July 31, 2025)
- Simplified from multi-stage supervisor approach to single-stage deployment
- Frontend is built as static export (`next export`) and served directly by FastAPI
- Single container exposes port 8000 for both API and static files
- Optimized for Google Cloud Run and Azure Container Instances

### MCP Version Pinning (July 31, 2025)
- **Issue**: MCP library updated from 1.12.2 to 1.12.3 on July 31, 2025
- **Breaking Change**: FastMCP no longer accepts `version` parameter in constructor
- **Solution**: Pin MCP to version 1.12.2 in `pyproject.toml` and use `uvx --with mcp==1.12.2` when launching semgrep-mcp
- **Reason**: semgrep-mcp v0.4.1 still passes the `version` parameter, causing TypeError with MCP 1.12.3

## Development Setup

### Environment Variables
Required in `.env` file:
- `OPENAI_API_KEY` - For OpenAI API access
- `SEMGREP_APP_TOKEN` - For Semgrep analysis

### Local Development
```bash
# Backend
cd backend
uv run server.py

# Frontend (in separate terminal)
cd frontend
npm run dev
```

### Docker Commands
```bash
# Build
docker build -t cyber-analyzer .

# Run with env file
docker run --rm -d --name cyber-analyzer -p 8000:8000 --env-file .env cyber-analyzer

# Logs
docker logs cyber-analyzer

# Stop
docker stop cyber-analyzer
```

## Important Implementation Details

1. **Static File Serving**: FastAPI serves the Next.js static export from the `static` directory. The `/health` endpoint must be defined before mounting static files to avoid route conflicts.

2. **API Routes**: All API endpoints are under `/api/` prefix (e.g., `/api/analyze`)

3. **Frontend Configuration**: 
   - `next.config.ts` uses `output: 'export'` for static generation
   - `trailingSlash: true` for proper routing
   - `images.unoptimized: true` for static export compatibility

## Known Issues & Workarounds

1. **MCP Version Compatibility**: Must use MCP 1.12.2 until semgrep-mcp is updated to remove the `version` parameter from FastMCP initialization.

## Testing & Quality
- Run `npm run lint` in frontend for linting
- Run `npm run typecheck` in frontend for type checking
- Backend uses `uv` for dependency management

## Future Considerations
- Monitor semgrep-mcp updates for compatibility with MCP 1.12.3+
- Consider adding automated tests
- May need to adjust Docker health check timeout for cloud deployments

## Cloud Deployment Project (Started July 31, 2025)

### Educational Objectives
- Teach students practical cloud deployment skills on Azure and GCP
- Compare/contrast serverless container platforms (Azure Container Apps vs Cloud Run)
- Hands-on experience with Terraform for infrastructure as code
- Understanding of cloud security, secrets management, and cost optimization

### Deployment Strategy
1. **Phase 1 - Azure Deployment**
   - Azure Container Apps (serverless container platform)
   - Azure Container Registry for image storage
   - Azure Key Vault for secrets management
   - Student accounts via Azure for Students ($100 credit)

2. **Phase 2 - GCP Deployment**
   - Google Cloud Run (equivalent to Azure Container Apps)
   - Artifact Registry for container images
   - Secret Manager for environment variables
   - Student accounts via GCP Free Tier + $300 credit

3. **Infrastructure as Code**
   - Terraform with workspaces to manage both clouds
   - Modular design for reusable components
   - Clear separation between Azure and GCP configurations

### Teaching Approach
- Start with Azure (less familiar to most students)
- Progress to GCP for comparison
- Focus on practical skills: account setup, cost management, security
- Emphasis on understanding trade-offs between platforms

### Prerequisites Covered in Previous Classes
- AWS App Runner deployment
- Basic Terraform concepts
- Container fundamentals

### Current Status (Updated July 31, 2025)
- ✅ **Azure deployment completed** - Application successfully deployed to Azure Container Apps
- ✅ **Docker image optimized** - Multi-stage build with ARM64→AMD64 cross-compilation for cloud compatibility
- ✅ **Terraform deployment pipeline** - Working infrastructure-as-code setup with Azure workspace
- ✅ **CORS and API routing resolved** - Frontend uses relative URLs in production, localhost in development
- ✅ **MCP server issue RESOLVED** - Increased memory to 2.0Gi fixed Semgrep SIGKILL issue

### MCP Server Memory Issue - RESOLVED (July 31, 2025)
**Issue**: Semgrep MCP server was getting SIGKILL (-9) on Azure when loading rule registry
- `list_tools` worked but `semgrep_scan` failed with exit code -9
- Process killed right after "Loading rules from registry..."
- **Root cause**: Insufficient memory allocation (1.0Gi) 
- **Solution**: Increased container memory from 1.0Gi to 2.0Gi and CPU from 0.5 to 1.0
- **Verified**: Works on both Azure Container Apps and Azure Container Instances with 2GB RAM
- **Status**: ACI test resources destroyed, but terraform config kept in `azure-aci/` for future reference

**Key lesson**: Semgrep rule registry loading is memory-intensive and requires at least 2GB RAM in cloud environments

### Key Deployment Lessons Learned
1. **Terraform Docker Provider Limitations**: 
   - Doesn't automatically detect source code changes
   - Must use `terraform taint` to force rebuilds when code changes
   - Using unique image tags can help avoid caching issues

2. **Frontend API URL Configuration**:
   - Next.js static export needs relative URLs for same-domain deployment
   - Environment-based logic: localhost in dev, relative URLs in production
   - CORS must allow wildcard origins when serving frontend from same domain

3. **Azure Container Apps Behavior**:
   - FQDN changes with each new revision (--0000001, --0000002, etc.)
   - Apps scale to zero automatically, saving costs
   - Logs accessible via `az containerapp logs show`

4. **Cross-Platform Docker Builds**:
   - M1 Mac builds ARM64 by default, Azure needs AMD64
   - Solution: `platform = "linux/amd64"` in Terraform Docker build
   - Slight performance penalty on M1 Macs but ensures compatibility