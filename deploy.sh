#!/bin/bash

# Medical AI Engine - Deployment Script
# Supports: Railway, Heroku, Docker, AWS EC2

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"
    
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        exit 1
    fi
    print_success "Python 3 found"
    
    if ! command -v pip3 &> /dev/null; then
        print_error "pip3 is not installed"
        exit 1
    fi
    print_success "pip3 found"
    
    if ! command -v git &> /dev/null; then
        print_error "git is not installed"
        exit 1
    fi
    print_success "git found"
}

# Setup environment
setup_environment() {
    print_header "Setting Up Environment"
    
    if [ ! -f .env ]; then
        print_warning ".env file not found, creating from .env.example"
        cp .env.example .env
        print_warning "Please edit .env with your configuration"
        exit 1
    fi
    
    print_success "Environment file found"
}

# Install dependencies
install_dependencies() {
    print_header "Installing Dependencies"
    
    pip3 install --upgrade pip
    pip3 install -r requirements.txt
    
    print_success "Dependencies installed"
}

# Test locally
test_locally() {
    print_header "Testing Locally"
    
    print_warning "Starting local server..."
    timeout 10 python3 main.py server --host localhost --port 8000 &
    sleep 3
    
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        print_success "Local server health check passed"
    else
        print_error "Local server health check failed"
        exit 1
    fi
    
    pkill -f "python3 main.py server" || true
}

# Deploy to Railway
deploy_railway() {
    print_header "Deploying to Railway"
    
    if ! command -v railway &> /dev/null; then
        print_warning "Railway CLI not found. Installing..."
        npm install -g @railway/cli
    fi
    
    print_warning "Please ensure you're logged into Railway"
    print_warning "Run: railway login"
    
    read -p "Continue with Railway deployment? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        railway up
        print_success "Deployed to Railway"
        
        # Get the URL
        RAILWAY_URL=$(railway env | grep RAILWAY_STATIC_URL | cut -d= -f2)
        print_success "Your API URL: $RAILWAY_URL"
    fi
}

# Deploy to Heroku
deploy_heroku() {
    print_header "Deploying to Heroku"
    
    if ! command -v heroku &> /dev/null; then
        print_warning "Heroku CLI not found. Installing..."
        curl https://cli-assets.heroku.com/install.sh | sh
    fi
    
    read -p "Enter Heroku app name: " HEROKU_APP
    
    if [ -z "$HEROKU_APP" ]; then
        print_error "App name cannot be empty"
        exit 1
    fi
    
    heroku login
    heroku create $HEROKU_APP || true
    
    # Set environment variables
    print_warning "Setting environment variables..."
    heroku config:set DEEPSEEK_API_KEY=$(grep DEEPSEEK_API_KEY .env | cut -d= -f2) --app $HEROKU_APP
    heroku config:set ENVIRONMENT=production --app $HEROKU_APP
    heroku config:set LOG_LEVEL=INFO --app $HEROKU_APP
    
    # Deploy
    git push heroku main
    
    print_success "Deployed to Heroku"
    print_success "Your API URL: https://$HEROKU_APP.herokuapp.com"
}

# Deploy with Docker
deploy_docker() {
    print_header "Deploying with Docker"
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi
    
    print_warning "Building Docker image..."
    docker build -t medical-ai-engine:latest .
    print_success "Docker image built"
    
    print_warning "Starting container..."
    docker run -d \
        -p 8000:8000 \
        --env-file .env \
        -v $(pwd)/data:/app/data \
        --name medical-ai-engine \
        --restart unless-stopped \
        medical-ai-engine:latest
    
    print_success "Container started"
    print_success "Your API URL: http://localhost:8000"
}

# Deploy to AWS EC2
deploy_aws() {
    print_header "Deploying to AWS EC2"
    
    read -p "Enter EC2 instance IP/hostname: " EC2_HOST
    read -p "Enter EC2 key file path: " EC2_KEY
    read -p "Enter EC2 username (default: ubuntu): " EC2_USER
    EC2_USER=${EC2_USER:-ubuntu}
    
    if [ -z "$EC2_HOST" ] || [ -z "$EC2_KEY" ]; then
        print_error "EC2 host and key are required"
        exit 1
    fi
    
    print_warning "Copying files to EC2..."
    scp -i $EC2_KEY -r . $EC2_USER@$EC2_HOST:/home/$EC2_USER/medical-ai-engine
    
    print_warning "Installing dependencies on EC2..."
    ssh -i $EC2_KEY $EC2_USER@$EC2_HOST << 'EOF'
        cd ~/medical-ai-engine
        sudo apt update
        sudo apt install -y python3-pip
        pip3 install -r requirements.txt
        
        # Start service
        nohup python3 main.py server --host 0.0.0.0 --port 8000 > server.log 2>&1 &
    EOF
    
    print_success "Deployed to AWS EC2"
    print_success "Your API URL: http://$EC2_HOST:8000"
}

# Main menu
show_menu() {
    print_header "Medical AI Engine - Deployment"
    echo ""
    echo "Select deployment option:"
    echo "1) Railway (Recommended)"
    echo "2) Heroku"
    echo "3) Docker (Local)"
    echo "4) AWS EC2"
    echo "5) Test Locally Only"
    echo "6) Exit"
    echo ""
    read -p "Enter choice (1-6): " choice
}

# Main execution
main() {
    check_prerequisites
    setup_environment
    install_dependencies
    
    while true; do
        show_menu
        
        case $choice in
            1)
                deploy_railway
                break
                ;;
            2)
                deploy_heroku
                break
                ;;
            3)
                deploy_docker
                break
                ;;
            4)
                deploy_aws
                break
                ;;
            5)
                test_locally
                print_success "Local testing completed"
                break
                ;;
            6)
                print_warning "Exiting..."
                exit 0
                ;;
            *)
                print_error "Invalid choice"
                ;;
        esac
    done
    
    print_header "Deployment Complete!"
    echo ""
    echo "Next steps:"
    echo "1. Update OKSmed app with your API URL"
    echo "2. Test the connection in app settings"
    echo "3. Start extracting medical questions!"
    echo ""
}

# Run main function
main "$@"
