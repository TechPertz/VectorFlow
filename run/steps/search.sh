#!/bin/bash

search() {
  show_header
  printf "${YELLOW}Vector Search${NC}\n\n"
  
  # Check for library ID
  if [ -z "$LIB_ID" ]; then
    printf "${RED}No library ID specified.${NC}\n"
    read -p "Enter library ID (or type 'back' to return): " LIB_ID
    check_back "$LIB_ID" && return 1
  fi
  
  # Check the index status first
  printf "Checking index status for library ${BLUE}$LIB_ID${NC}...\n"
  INDEX_STATUS_RESPONSE=$(curl -s "http://localhost:8000/libraries/$LIB_ID/index")
  
  if echo "$INDEX_STATUS_RESPONSE" | grep -q "detail"; then
    printf "${RED}Error checking index status:${NC}\n"
    echo "$INDEX_STATUS_RESPONSE" | jq -r '.detail'
    read -p "Press Enter to continue (or type 'back' to return to menu): " INPUT
    check_back "$INPUT" && return 1
    return 0
  fi
  
  INDEX_STATUS=$(echo "$INDEX_STATUS_RESPONSE" | jq -r '.status')
  
  if [ "$INDEX_STATUS" = "none" ]; then
    printf "${RED}Library has no index. Please build an index first.${NC}\n"
    read -p "Do you want to build an index now? (y/n): " BUILD_NOW
    if [[ "$BUILD_NOW" =~ ^[Yy]$ ]]; then
      build_index
      return $?
    else
      read -p "Press Enter to continue (or type 'back' to return to menu): " INPUT
      check_back "$INPUT" && return 1
      return 0
    fi
  elif [ "$INDEX_STATUS" = "needs_rebuild" ] || [ "$INDEX_STATUS" = "modified" ]; then
    printf "${YELLOW}Index status: $INDEX_STATUS${NC}\n"
    printf "${YELLOW}The search will automatically handle incremental updates.${NC}\n"
  else
    printf "${GREEN}Index status: $INDEX_STATUS${NC}\n"
  fi
  
  printf "\nChoose search type:\n"
  printf "1) Text search (convert text to embeddings)\n"
  printf "2) Vector search (provide embedding directly)\n"
  read -p "Your choice (1-2): " SEARCH_TYPE
  check_back "$SEARCH_TYPE" && return 1
  
  # Always use rebuild_if_needed for better user experience
  REBUILD_IF_NEEDED="true"
  
  if [ "$SEARCH_TYPE" = "1" ]; then
    # Text search
    read -p "Enter your search query: " QUERY_TEXT
    check_back "$QUERY_TEXT" && return 1
    
    printf "Performing text search for: ${BLUE}$QUERY_TEXT${NC}\n"
    
    RESPONSE=$(curl -s -X POST \
      "http://localhost:8000/libraries/$LIB_ID/text-search?rebuild_if_needed=$REBUILD_IF_NEEDED" \
      -H "Content-Type: application/json" \
      -H "accept: application/json" \
      -d "{\"text\":\"$QUERY_TEXT\"}")
    
    if echo "$RESPONSE" | grep -q "detail"; then
      printf "${RED}Error during search:${NC}\n"
      echo "$RESPONSE" | jq -r '.detail'
    else
      printf "${GREEN}Search results:${NC}\n"
      COUNT=$(echo "$RESPONSE" | jq -r '.results_count')
      printf "Found ${BLUE}$COUNT${NC} results\n\n"
      
      echo "$RESPONSE" | jq -r '.results[] | "ID: \(.id)\nText: \(.text)\n"'
    fi
    
  else
    # Vector search (using a sample embedding for demo)
    printf "For demonstration, using a sample embedding vector\n"
    printf "(In a real application, you would provide your own embeddings)\n"
    
    # Generate a random embedding for demo purposes
    EMBEDDING="["
    for i in {1..1536}; do
      EMBEDDING+="$(awk -v min=-1 -v max=1 'BEGIN{srand(); print min+rand()*(max-min)}')"
      if [ $i -lt 1536 ]; then
        EMBEDDING+=", "
      fi
    done
    EMBEDDING+="]"
    
    printf "Performing vector search...\n"
    
    RESPONSE=$(curl -s -X POST \
      "http://localhost:8000/libraries/$LIB_ID/search?rebuild_if_needed=$REBUILD_IF_NEEDED" \
      -H "Content-Type: application/json" \
      -H "accept: application/json" \
      -d "$EMBEDDING")
    
    if echo "$RESPONSE" | grep -q "detail"; then
      printf "${RED}Error during search:${NC}\n"
      echo "$RESPONSE" | jq -r '.detail'
    else
      printf "${GREEN}Search results:${NC}\n"
      COUNT=$(echo "$RESPONSE" | jq length)
      printf "Found ${BLUE}$COUNT${NC} results\n\n"
      
      echo "$RESPONSE" | jq -r '.[] | "ID: \(.id)\nText: \(.text)\n"'
    fi
  fi
  
  read -p "Press Enter to continue (or type 'back' to return to menu): " INPUT
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