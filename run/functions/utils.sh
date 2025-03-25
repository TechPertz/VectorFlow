#!/bin/bash

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' 

LIB_ID=""
DOC_ID=""
LIB_NAME="Science Papers"
LIB_DESC="AI Research Papers"
DOC_TITLE="Transformer Architecture"
DOC_AUTHOR="Vaswani et al."
EMBEDDING_CHOICE=1
K_VALUE=3
K_VALUE2=3
SEARCH_QUERY="How do transformer models use attention?"
SEARCH_QUERY2="What is tokenization in NLP?"
ALGORITHM="kd_tree"

show_help() {
  printf "${YELLOW}VECTORFLOW DEMO INSTRUCTIONS:${NC}\n"
  printf "=========================\n"
  
  printf "\n${YELLOW}Recommended flow of steps:${NC}\n"
  printf "1. Create a library (container for documents)\n"
  printf "2. Create a document (container for chunks)\n"
  printf "3. Add chunks with embeddings (vector representations of text)\n"
  printf "4. Build a vector index (for efficient similarity search)\n"
  printf "5. Perform vector searches (find similar content)\n"
  printf "6. Perform different search using alternative method\n"
  printf "7. List documents in a library\n"
  printf "8. List all libraries\n"
  printf "9. List chunks in a document\n"
  
  printf "\n${YELLOW}Navigation tips:${NC}\n"
  printf "- Type '${BLUE}back${NC}' at any prompt to return to the main menu\n"
  printf "- Type '${BLUE}exit${NC}' to quit the program completely\n"
  printf "- Press Enter at most prompts to use the default value shown in [brackets]\n"
}

check_back() {
  local input="$1"
  
  input=$(echo "$input" | tr '[:upper:]' '[:lower:]')
  if [[ "$input" == "back" ]]; then
    printf "${BLUE}Returning to main menu...${NC}\n"
    return 0
  fi
  return 1
}

show_header() {
  clear
  printf "${GREEN}===============================================${NC}\n"
  printf "${GREEN}      VectorFlow Interactive Demo Script       ${NC}\n"
  printf "${GREEN}===============================================${NC}\n\n"
} 