#!/bin/bash

build_index() {
  show_header
  printf "${YELLOW}Building a Vector Index${NC}\n\n"
  
  # Check for library ID
  if [ -z "$LIB_ID" ]; then
    printf "${RED}No library ID specified.${NC}\n"
    read -p "Enter library ID (or type 'back' to return): " LIB_ID
    check_back "$LIB_ID" && return 1
  fi
  
  printf "Building an index for library: ${BLUE}$LIB_ID${NC}\n"
  
  # First, check the current index status
  printf "Checking current index status...\n"
  INDEX_STATUS=$(curl -s "http://localhost:8000/libraries/$LIB_ID/index" | jq -r '.status')
  INDEX_ALGO=$(curl -s "http://localhost:8000/libraries/$LIB_ID/index" | jq -r '.algorithm')
  
  printf "Current index status: "
  if [ "$INDEX_STATUS" = "current" ]; then
    printf "${GREEN}$INDEX_STATUS${NC}\n"
    printf "Current algorithm: ${BLUE}$INDEX_ALGO${NC}\n"
    
    read -p "Index is up to date. Do you want to rebuild it anyway? (y/n): " REBUILD
    if [[ ! "$REBUILD" =~ ^[Yy]$ ]]; then
      read -p "Press Enter to continue (or type 'back' to return to menu): " INPUT
      check_back "$INPUT" && return 1
      return 0
    fi
  elif [ "$INDEX_STATUS" = "modified" ]; then
    printf "${YELLOW}$INDEX_STATUS${NC}\n"
    printf "Current algorithm: ${BLUE}$INDEX_ALGO${NC}\n"
    printf "Using incremental update with algorithm: ${BLUE}$INDEX_ALGO${NC}\n"
    
    # Automatically use incremental update
    RESPONSE=$(curl -s -X POST \
      "http://localhost:8000/libraries/$LIB_ID/index?algorithm=$INDEX_ALGO&force=false" \
      -H "Content-Type: application/json" \
      -H "accept: application/json")
      
    if echo "$RESPONSE" | grep -q "message"; then
      MESSAGE=$(echo "$RESPONSE" | jq -r '.message')
      printf "${GREEN}$MESSAGE${NC}\n"
    else
      printf "${RED}Error updating index:${NC}\n"
      echo "$RESPONSE" | jq
    fi
    
    read -p "Press Enter to continue (or type 'back' to return to menu): " INPUT
    check_back "$INPUT" && return 1
    return 0
  elif [ "$INDEX_STATUS" = "needs_rebuild" ]; then
    printf "${RED}$INDEX_STATUS${NC}\n"
    if [ "$INDEX_ALGO" != "null" ]; then
      printf "Current algorithm: ${BLUE}$INDEX_ALGO${NC}\n"
    fi
    printf "Index needs to be rebuilt due to significant changes\n"
  elif [ "$INDEX_STATUS" = "none" ]; then
    printf "${RED}$INDEX_STATUS${NC}\n"
    printf "No index exists yet\n"
  else
    printf "${RED}Unknown status: $INDEX_STATUS${NC}\n"
  fi
  
  # Show algorithm options
  printf "${YELLOW}Select an algorithm:${NC}\n"
  printf "1) Linear (Default, works with any data)\n"
  printf "2) KDTree (Good for smaller dimensions, faster search)\n"
  printf "3) LSH (Locality Sensitive Hashing, best for high dimensions)\n"
  read -p "Your choice (1-3, default 1): " ALGO_CHOICE
  check_back "$ALGO_CHOICE" && return 1
  
  ALGORITHM="linear"
  case $ALGO_CHOICE in
    2) ALGORITHM="kd_tree" ;;
    3) ALGORITHM="lsh" ;;
    *) ALGORITHM="linear" ;;
  esac
  
  # Set force parameter based on current state
  FORCE="false"
  if [ "$INDEX_STATUS" = "current" ]; then
    # Only when explicitly rebuilding a current index we should force it
    FORCE="true"
  fi
  
  # Build the index
  printf "Building ${BLUE}$ALGORITHM${NC} index for library ${BLUE}$LIB_ID${NC}...\n"
  
  RESPONSE=$(curl -s -X POST \
    "http://localhost:8000/libraries/$LIB_ID/index?algorithm=$ALGORITHM&force=$FORCE" \
    -H "Content-Type: application/json" \
    -H "accept: application/json")
    
  if echo "$RESPONSE" | grep -q "message"; then
    MESSAGE=$(echo "$RESPONSE" | jq -r '.message')
    printf "${GREEN}$MESSAGE${NC}\n"
  else
    printf "${RED}Error building index:${NC}\n"
    echo "$RESPONSE" | jq
  fi
  
  read -p "Press Enter to continue (or type 'back' to return to menu): " INPUT
  check_back "$INPUT" && return 1
  return 0
} 