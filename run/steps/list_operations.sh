#!/bin/bash

list_documents() {
  if [ -z "$LIB_ID" ]; then
    printf "${RED}Error: You need to create a library first (Step 1)${NC}\n"
    read -p "Press Enter to continue (or type 'back'): " INPUT
    check_back "$INPUT" && return 1
    return 0
  fi

  printf "\n${BLUE}STEP 7: Listing all documents in a library${NC}\n"
  printf "Retrieving all documents from library: $LIB_ID\n"
  printf "${YELLOW}To return to the main menu, type 'back' and press Enter.${NC}\n\n"
  
  curl -s -X GET "http://localhost:8000/libraries/$LIB_ID/documents" | jq '.'
  
  read -p "Press Enter to continue (or type 'back'): " INPUT
  check_back "$INPUT" && return 1
  
  return 0
}

list_libraries() {
  printf "\n${BLUE}STEP 8: Listing all libraries${NC}\n"
  printf "Retrieving all libraries from the database\n"
  printf "${YELLOW}To return to the main menu, type 'back' and press Enter.${NC}\n\n"

  
  RESPONSE=$(curl -s -X GET "http://localhost:8000/libraries/" \
    -H "accept: application/json")
  
  
  printf "${YELLOW}DEBUG - Number of libraries: $(echo "$RESPONSE" | jq '. | length')${NC}\n"
  printf "${YELLOW}DEBUG - Library IDs: $(echo "$RESPONSE" | jq '.[].id')${NC}\n"
  
  
  echo "$RESPONSE" | jq '.'
  
  read -p "Press Enter to continue (or type 'back'): " INPUT
  check_back "$INPUT" && return 1
  
  return 0
}

list_chunks() {
  if [ -z "$DOC_ID" ] || [ -z "$LIB_ID" ]; then
    printf "${RED}Error: You need to create a library and document first (Steps 1-2)${NC}\n"
    read -p "Press Enter to continue (or type 'back'): " INPUT
    check_back "$INPUT" && return 1
    return 0
  fi

  printf "\n${BLUE}STEP 9: Listing all chunks in a document${NC}\n"
  printf "Retrieving all chunks from document: $DOC_ID\n"
  printf "${YELLOW}To return to the main menu, type 'back' and press Enter.${NC}\n\n"
  
  
  curl -s -X GET "http://localhost:8000/libraries/$LIB_ID/documents/$DOC_ID/chunks" | jq '.'
  
  read -p "Press Enter to continue (or type 'back'): " INPUT
  check_back "$INPUT" && return 1
  
  return 0
}

show_index_status() {
  show_header
  printf "${YELLOW}Showing Index Status${NC}\n\n"
  
  if [ -z "$LIB_ID" ]; then
    printf "${RED}No library ID specified${NC}\n"
    read -p "Enter library ID (or type 'back' to return): " LIB_ID
    check_back "$LIB_ID" && return 1
  fi
  
  printf "Getting index status for library: ${BLUE}$LIB_ID${NC}\n\n"
  
  RESPONSE=$(curl -s "http://localhost:8000/libraries/$LIB_ID/index")
  
  if echo "$RESPONSE" | grep -q "detail"; then
    printf "${RED}Error:${NC}\n"
    echo "$RESPONSE" | jq -r '.detail'
  else
    STATUS=$(echo "$RESPONSE" | jq -r '.status')
    ALGORITHM=$(echo "$RESPONSE" | jq -r '.algorithm')
    
    printf "Index Status: "
    if [ "$STATUS" = "current" ]; then
      printf "${GREEN}$STATUS${NC}\n"
    elif [ "$STATUS" = "modified" ]; then
      printf "${YELLOW}$STATUS${NC}\n"
    elif [ "$STATUS" = "needs_rebuild" ]; then
      printf "${RED}$STATUS${NC}\n"
    else
      printf "${RED}$STATUS${NC}\n"
    fi
    
    if [ "$ALGORITHM" != "null" ]; then
      printf "Algorithm: ${BLUE}$ALGORITHM${NC}\n"
    fi
    
    printf "\nDetailed statistics:\n"
    echo "$RESPONSE" | jq '.stats'
    
    if [ "$STATUS" = "modified" ] || [ "$STATUS" = "needs_rebuild" ]; then
      printf "\n${YELLOW}Index needs updating. Do you want to rebuild it now?${NC} (y/n): "
      read REBUILD
      if [[ "$REBUILD" =~ ^[Yy]$ ]]; then
        build_index
        return $?
      fi
    fi
  fi
  
  read -p "Press Enter to continue (or type 'back' to return to menu): " INPUT
  check_back "$INPUT" && return 1
  return 0
} 