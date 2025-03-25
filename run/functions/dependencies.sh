#!/bin/bash

check_dependencies() {
  printf "${BLUE}Checking dependencies...${NC}\n"
  
  
  if ! command -v curl &> /dev/null; then
    printf "${YELLOW}curl not found. Attempting to install...${NC}\n"
    
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
      
      if command -v brew &> /dev/null; then
        brew install curl
      else
        printf "${RED}Homebrew not found. Please install curl manually:${NC}\n"
        printf "brew install curl\n"
        exit 1
      fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
      
      if command -v apt-get &> /dev/null; then
        sudo apt-get update && sudo apt-get install -y curl
      elif command -v yum &> /dev/null; then
        sudo yum install -y curl
      elif command -v dnf &> /dev/null; then
        sudo dnf install -y curl
      else
        printf "${RED}Package manager not found. Please install curl manually.${NC}\n"
        exit 1
      fi
    else
      printf "${RED}Unsupported OS. Please install curl manually.${NC}\n"
      exit 1
    fi
  fi
  
  
  if ! command -v jq &> /dev/null; then
    printf "${YELLOW}jq not found. Attempting to install...${NC}\n"
    
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
      
      if command -v brew &> /dev/null; then
        brew install jq
      else
        printf "${RED}Homebrew not found. Please install jq manually:${NC}\n"
        printf "brew install jq\n"
        exit 1
      fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
      
      if command -v apt-get &> /dev/null; then
        sudo apt-get update && sudo apt-get install -y jq
      elif command -v yum &> /dev/null; then
        sudo yum install -y jq
      elif command -v dnf &> /dev/null; then
        sudo dnf install -y jq
      else
        printf "${RED}Package manager not found. Please install jq manually.${NC}\n"
        exit 1
      fi
    else
      printf "${RED}Unsupported OS. Please install jq manually.${NC}\n"
      exit 1
    fi
  fi
  
  printf "${GREEN}All dependencies are installed!${NC}\n"
}

check_api_server() {
  printf "${BLUE}Checking if VectorFlow API server is running...${NC}\n"
  
  
  if curl -s -f "http://localhost:8000/" > /dev/null; then
    printf "${GREEN}API server is running!${NC}\n"
  else
    printf "${RED}Cannot connect to API server at http://localhost:8000/${NC}\n"
    printf "${YELLOW}Please make sure the VectorFlow API server is running before proceeding.${NC}\n"
    printf "You can start it with: uvicorn app.main:app --reload\n"
    
    read -p "Do you want to continue anyway? (y/n) [n]: " CONTINUE
    CONTINUE=${CONTINUE:-n}
    if [[ "${CONTINUE,,}" != "y" ]]; then
      exit 1
    fi
  fi
} 