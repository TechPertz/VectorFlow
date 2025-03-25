#!/bin/bash

search() {
  show_header
  printf "${YELLOW}STEP 5: Performing search${NC}\n"
  printf "To return to the main menu, type 'back' and press Enter.\n\n"
  
  
  if [ -z "$DOC_ID" ]; then
    printf "${RED}Error: Document ID is not set. Please create a document first.${NC}\n"
    read -p "Press Enter to continue (or type 'back'): " INPUT
    check_back "$INPUT" && return 1
    return 0
  fi
  
  
  if [ -z "$LIB_ID" ]; then
    printf "${RED}Error: Library ID is not set. Please create a library first.${NC}\n"
    read -p "Press Enter to continue (or type 'back'): " INPUT
    check_back "$INPUT" && return 1
    return 0
  fi
  
  
  printf "Would you like to use a sample query or enter your own?\n"
  printf "1. Use sample query: \"transformer models\"\n"
  printf "2. Use sample query: \"attention mechanisms\"\n" 
  printf "3. Use sample query: \"embeddings and vector representations\"\n"
  printf "4. Enter your own query\n"
  read -p "Enter your choice (1-4) [1] (or type 'back'): " QUERY_CHOICE
  check_back "$QUERY_CHOICE" && return 1
  QUERY_CHOICE=${QUERY_CHOICE:-1}
  
  
  case $QUERY_CHOICE in
    1) QUERY="transformer models" ;;
    2) QUERY="attention mechanisms" ;;
    3) QUERY="embeddings and vector representations" ;;
    4) 
      read -p "Enter your search query: " QUERY
      check_back "$QUERY" && return 1
      ;;
    *) 
      printf "${RED}Invalid choice. Using default: \"transformer models\"${NC}\n"
      QUERY="transformer models"
      ;;
  esac
  
  
  read -p "How many results do you want to retrieve? [3] (or type 'back'): " TOP_K
  check_back "$TOP_K" && return 1
  TOP_K=${TOP_K:-3}
  
  printf "Searching for: \"${QUERY}\"...\n"
  
  
  RESPONSE=$(curl -L -s -X POST "http://localhost:8000/libraries/$LIB_ID/text-search?k=$TOP_K" \
    -H "Content-Type: application/json" \
    -d "{\"text\": \"$QUERY\"}")
  
  
  echo "$RESPONSE"
  
  read -p "Press Enter to continue (or type 'back'): " INPUT
  check_back "$INPUT" && return 1
  
  return 0
}

first_search() {
  search
  return $?
}

second_search() {
  search
  return $?
} 