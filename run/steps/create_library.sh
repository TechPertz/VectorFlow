#!/bin/bash

create_library() {
  printf "${BLUE}STEP 1: Creating a vector library${NC}\n"
  printf "We need to create a vector database library to store your embeddings.\n"
  printf "${YELLOW}To return to the main menu at any time, just type 'back' and press Enter.${NC}\n\n"
  read -p "Enter a name for your library [$LIB_NAME] (or type 'back'): " INPUT
  
  
  if [ -z "$INPUT" ]; then
    INPUT="$LIB_NAME"
  fi
  
  
  check_back "$INPUT" && return 1
  
  
  LIB_NAME="$INPUT"
  
  read -p "Enter a description [$LIB_DESC] (or type 'back'): " INPUT
  
  
  if [ -z "$INPUT" ]; then
    INPUT="$LIB_DESC"
  fi
  
  
  check_back "$INPUT" && return 1
  
  
  LIB_DESC="$INPUT"

  read -p "Press Enter to create the library (or type 'back'): " INPUT
  
  check_back "$INPUT" && return 1

  
  printf "Creating library with name: ${GREEN}$LIB_NAME${NC} and description: ${GREEN}$LIB_DESC${NC}\n"
  LIB_ID=$(curl -L -s -X POST http://localhost:8000/libraries/ \
    -H "Content-Type: application/json" \
    -d "{\"name\": \"$LIB_NAME\", \"metadata\": {\"description\": \"$LIB_DESC\"}}" | jq -r .id)
  echo "Library created with ID: $LIB_ID"
  
  read -p "Press Enter to continue (or type 'back'): " INPUT
  check_back "$INPUT" && return 1
  
  return 0
} 