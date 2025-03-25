#!/bin/bash

create_document() {
  if [ -z "$LIB_ID" ]; then
    printf "${RED}Error: You need to create a library first (Step 1)${NC}\n"
    read -p "Press Enter to continue (or type 'back'): " INPUT
    check_back "$INPUT" && return 1
    return 0
  fi

  printf "\n${BLUE}STEP 2: Creating a document${NC}\n"
  printf "Documents group related chunks of text and embeddings.\n"
  printf "${YELLOW}To return to the main menu at any time, just type 'back' and press Enter.${NC}\n\n"
  read -p "Enter a title for your document [$DOC_TITLE] (or type 'back'): " INPUT
  
  
  if [ -z "$INPUT" ]; then
    INPUT="$DOC_TITLE"
  fi
  
  
  check_back "$INPUT" && return 1
  
  
  DOC_TITLE="$INPUT"
  
  read -p "Enter an author name [$DOC_AUTHOR] (or type 'back'): " INPUT
  
  
  if [ -z "$INPUT" ]; then
    INPUT="$DOC_AUTHOR"
  fi
  
  
  check_back "$INPUT" && return 1
  
  
  DOC_AUTHOR="$INPUT"

  read -p "Press Enter to create the document (or type 'back'): " INPUT
  
  check_back "$INPUT" && return 1

  
  printf "Creating document with title: ${GREEN}$DOC_TITLE${NC} and author: ${GREEN}$DOC_AUTHOR${NC}\n"
  RESPONSE=$(curl -L -s -w "\n%{http_code}" -X POST http://localhost:8000/libraries/$LIB_ID/documents \
    -H "Content-Type: application/json" \
    -d "{\"metadata\": {\"title\": \"$DOC_TITLE\", \"author\": \"$DOC_AUTHOR\"}}")
  
  HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
  BODY=$(echo "$RESPONSE" | sed '$d')
  
  if [ "$HTTP_CODE" -eq 201 ] || [ "$HTTP_CODE" -eq 200 ]; then
    DOC_ID=$(echo "$BODY" | jq -r .id)
    echo "Document created with ID: $DOC_ID"
  else
    ERROR_MSG=$(echo "$BODY" | jq -r .detail 2>/dev/null || echo "Unknown error")
    printf "${RED}Error creating document: $ERROR_MSG (HTTP $HTTP_CODE)${NC}\n"
    printf "${RED}The library ID $LIB_ID might be invalid or not exist.${NC}\n"
    DOC_ID=""
  fi
  
  read -p "Press Enter to continue (or type 'back'): " INPUT
  check_back "$INPUT" && return 1
  
  return 0
} 