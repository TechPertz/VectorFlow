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
  
  # Get query based on search type
  if [ "$SEARCH_TYPE" = "1" ]; then
    # Text search
    printf "\n${BLUE}Example search queries:${NC}\n"
    printf "1) How do transformer models use attention?\n"
    printf "2) What is tokenization in NLP?\n"
    printf "3) How does BERT improve language understanding?\n"
    printf "4) What is transfer learning in NLP?\n"
    printf "5) Custom query\n"
    read -p "Choose a query (1-5) or enter your own: " QUERY_CHOICE
    check_back "$QUERY_CHOICE" && return 1
    
    case $QUERY_CHOICE in
      1) QUERY_TEXT="How do transformer models use attention?" ;;
      2) QUERY_TEXT="What is tokenization in NLP?" ;;
      3) QUERY_TEXT="How does BERT improve language understanding?" ;;
      4) QUERY_TEXT="What is transfer learning in NLP?" ;;
      5) read -p "Enter your custom query: " QUERY_TEXT ;;
      *) QUERY_TEXT="$QUERY_CHOICE" ;;
    esac
    
    printf "Using search query: ${BLUE}$QUERY_TEXT${NC}\n\n"
  else
    # Vector search (using a sample embedding for demo)
    printf "For demonstration, using a sample embedding vector\n"
    printf "(In a real application, you would provide your own embeddings)\n\n"
    
    # Generate a random embedding for demo purposes
    EMBEDDING="["
    for i in {1..1536}; do
      EMBEDDING+="$(awk -v min=-1 -v max=1 'BEGIN{srand(); print min+rand()*(max-min)}')"
      if [ $i -lt 1536 ]; then
        EMBEDDING+=", "
      fi
    done
    EMBEDDING+="]"
  fi
  
  # Ask if user wants to apply metadata filtering
  printf "\n${YELLOW}=== Metadata Filtering ===${NC}\n"
  printf "Metadata filtering can narrow down results by properties like name or creation date\n\n"
  read -p "Do you want to filter results using metadata? (y/n): " USE_FILTER
  
  # Initialize metadata filter as empty JSON object
  METADATA_FILTER="{}"
  
  if [[ "$USE_FILTER" =~ ^[Yy]$ ]]; then
    # Build metadata filter dictionary
    FILTER_DICT=()
    
    printf "\n${BLUE}Metadata Filtering Examples:${NC}\n"
    printf "  - For basic search by name: name:abstract\n"
    printf "  - For dates from a certain point: created_at_after:2023-01-01\n"
    printf "  - For dates before a point: created_at_before:2025-01-01\n"
    printf "  - For text contains: name_contains:report\n\n"
    
    # First ask about name filtering
    read -p "Do you want to filter by name? (y/n): " FILTER_NAME
    if [[ "$FILTER_NAME" =~ ^[Yy]$ ]]; then
      read -p "Enter exact name to match: " NAME_VALUE
      if [ -n "$NAME_VALUE" ]; then
        FILTER_DICT+=("\"name\": \"$NAME_VALUE\"")
      fi
    fi
    
    # Then ask about creation date
    read -p "Do you want to filter by creation date after a certain date? (y/n): " FILTER_DATE
    if [[ "$FILTER_DATE" =~ ^[Yy]$ ]]; then
      read -p "Enter date in YYYY-MM-DD format: " DATE_VALUE
      if [ -n "$DATE_VALUE" ]; then
        if [[ "$DATE_VALUE" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
          # Add the _after suffix for the key (not in the JSON)
          FILTER_DICT+=("\"created_at_after\": \"$DATE_VALUE\"")
        else
          printf "${RED}Invalid date format. Using YYYY-MM-DD format.${NC}\n"
        fi
      fi
    fi
    
    # Ask about name contains
    read -p "Do you want to filter by text contained in name? (y/n): " FILTER_CONTAINS
    if [[ "$FILTER_CONTAINS" =~ ^[Yy]$ ]]; then
      read -p "Enter text to search for in name: " CONTAINS_VALUE
      if [ -n "$CONTAINS_VALUE" ]; then
        # Add the _contains suffix for the key
        FILTER_DICT+=("\"name_contains\": \"$CONTAINS_VALUE\"")
      fi
    fi
    
    # Build the JSON object from the collected filters
    if [ ${#FILTER_DICT[@]} -gt 0 ]; then
      METADATA_FILTER="{"
      for i in "${!FILTER_DICT[@]}"; do
        METADATA_FILTER+="${FILTER_DICT[$i]}"
        if [ $i -lt $(( ${#FILTER_DICT[@]} - 1 )) ]; then
          METADATA_FILTER+=", "
        fi
      done
      METADATA_FILTER+="}"
    fi
    
    printf "Using metadata filter: ${BLUE}$METADATA_FILTER${NC}\n\n"
  fi
  
  # Perform the search with metadata filter
  printf "${YELLOW}=== Performing Search ===${NC}\n"
  
  if [ "$SEARCH_TYPE" = "1" ]; then
    # Text search
    printf "Performing text search for: ${BLUE}$QUERY_TEXT${NC}\n"
    if [ "$METADATA_FILTER" != "{}" ]; then
      printf "With metadata filter: ${BLUE}$METADATA_FILTER${NC}\n"
    fi
    
    # Create the request body with text and metadata_filter
    REQUEST_BODY="{\"text\":\"$QUERY_TEXT\", \"metadata_filter\":$METADATA_FILTER}"
    
    # Debug: Show the request
    printf "\nSending request: ${BLUE}$REQUEST_BODY${NC}\n\n"
    
    RESPONSE=$(curl -s -X POST \
      "http://localhost:8000/libraries/$LIB_ID/text-search?rebuild_if_needed=$REBUILD_IF_NEEDED" \
      -H "Content-Type: application/json" \
      -H "accept: application/json" \
      -d "$REQUEST_BODY")
    
    if echo "$RESPONSE" | grep -q "detail"; then
      printf "${RED}Error during search:${NC}\n"
      echo "$RESPONSE" | jq || echo "$RESPONSE"
    else
      printf "\n${GREEN}=== Search Results ===${NC}\n"
      COUNT=$(echo "$RESPONSE" | jq -r '.results_count')
      
      if [ "$METADATA_FILTER" != "{}" ]; then
        printf "Found ${BLUE}$COUNT${NC} results with metadata filtering\n\n"
      else
        printf "Found ${BLUE}$COUNT${NC} results\n\n"
      fi
      
      if [ "$COUNT" -gt 0 ]; then
        echo "$RESPONSE" | jq -r '.results[] | "ID: \(.id)\nText: \(.text)\nMetadata: \(.metadata | @json)\n"'
      else
        printf "${YELLOW}No results found. Try a different query or adjust your metadata filters.${NC}\n"
      fi
    fi
  else
    # Vector search
    printf "Performing vector search with embedding...\n"
    if [ "$METADATA_FILTER" != "{}" ]; then
      printf "With metadata filter: ${BLUE}$METADATA_FILTER${NC}\n"
    fi
    
    # Create the request body with query and metadata_filter
    REQUEST_BODY="{\"query\":$EMBEDDING, \"metadata_filter\":$METADATA_FILTER}"
    
    # Debug: Show the request
    printf "\nSending request: ${BLUE}$REQUEST_BODY${NC}\n\n"
    
    RESPONSE=$(curl -s -X POST \
      "http://localhost:8000/libraries/$LIB_ID/search?rebuild_if_needed=$REBUILD_IF_NEEDED" \
      -H "Content-Type: application/json" \
      -H "accept: application/json" \
      -d "$REQUEST_BODY")
    
    if echo "$RESPONSE" | grep -q "detail"; then
      printf "${RED}Error during search:${NC}\n"
      echo "$RESPONSE" | jq || echo "$RESPONSE"
    else
      printf "\n${GREEN}=== Search Results ===${NC}\n"
      COUNT=$(echo "$RESPONSE" | jq length)
      
      if [ "$METADATA_FILTER" != "{}" ]; then
        printf "Found ${BLUE}$COUNT${NC} results with metadata filtering\n\n"
      else
        printf "Found ${BLUE}$COUNT${NC} results\n\n"
      fi
      
      if [ "$COUNT" -gt 0 ]; then
        echo "$RESPONSE" | jq -r '.[] | "ID: \(.id)\nText: \(.text)\nMetadata: \(.metadata | @json)\n"'
      else
        printf "${YELLOW}No results found. Try a different query or adjust your metadata filters.${NC}\n"
      fi
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