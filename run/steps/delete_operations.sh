#!/bin/bash

delete_library() {
  show_header
  printf "${YELLOW}Delete a Library${NC}\n\n"
  
  # Use existing library ID or ask for one
  if [ -z "$LIB_ID" ]; then
    read -p "Enter Library ID (or type 'back' to return): " LIB_ID
    check_back "$LIB_ID" && return 1
  else
    printf "Using existing Library ID: ${BLUE}$LIB_ID${NC}\n"
    read -p "Continue with this ID? (y/n, or 'back' to return): " CONFIRM
    check_back "$CONFIRM" && return 1
    
    if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
      read -p "Enter new Library ID (or type 'back' to return): " LIB_ID
      check_back "$LIB_ID" && return 1
    fi
  fi
  
  # Confirm deletion
  printf "${RED}WARNING: Deleting library $LIB_ID will remove all documents and chunks within it!${NC}\n"
  read -p "Are you sure you want to proceed? (y/n): " DELETE_CONFIRM
  
  if [[ ! "$DELETE_CONFIRM" =~ ^[Yy]$ ]]; then
    printf "${YELLOW}Deletion cancelled.${NC}\n"
    read -p "Press Enter to continue (or type 'back' to return to menu): " INPUT
    check_back "$INPUT" && return 1
    return 0
  fi
  
  # Proceed with deletion
  printf "Deleting library ${BLUE}$LIB_ID${NC}...\n"
  
  RESPONSE=$(curl -s -X DELETE \
    "http://localhost:8000/libraries/$LIB_ID" \
    -H "accept: application/json")
  
  if echo "$RESPONSE" | grep -q "\"status\":\"deleted\""; then
    printf "${GREEN}Library deleted successfully!${NC}\n"
    printf "${YELLOW}Note: Library ID has been cleared.${NC}\n"
    # Clear the library ID since it's now deleted
    LIB_ID=""
    DOC_ID=""
  else
    printf "${RED}Error deleting library:${NC}\n"
    echo "$RESPONSE" | jq
  fi
  
  read -p "Press Enter to continue (or type 'back' to return to menu): " INPUT
  check_back "$INPUT" && return 1
  return 0
}

delete_document() {
  show_header
  printf "${YELLOW}Delete a Document${NC}\n\n"
  
  # Check if library ID is set
  if [ -z "$LIB_ID" ]; then
    printf "${RED}Error: Library ID not set. Please set a library ID first.${NC}\n"
    read -p "Press Enter to continue (or type 'back' to return to menu): " INPUT
    check_back "$INPUT" && return 1
    return 0
  fi
  
  # Use existing document ID or ask for one
  if [ -z "$DOC_ID" ]; then
    read -p "Enter Document ID (or type 'back' to return): " DOC_ID
    check_back "$DOC_ID" && return 1
  else
    printf "Using existing Document ID: ${BLUE}$DOC_ID${NC}\n"
    read -p "Continue with this ID? (y/n, or 'back' to return): " CONFIRM
    check_back "$CONFIRM" && return 1
    
    if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
      read -p "Enter new Document ID (or type 'back' to return): " DOC_ID
      check_back "$DOC_ID" && return 1
    fi
  fi
  
  # Confirm deletion
  printf "${RED}WARNING: Deleting document $DOC_ID will remove all chunks within it!${NC}\n"
  read -p "Are you sure you want to proceed? (y/n): " DELETE_CONFIRM
  
  if [[ ! "$DELETE_CONFIRM" =~ ^[Yy]$ ]]; then
    printf "${YELLOW}Deletion cancelled.${NC}\n"
    read -p "Press Enter to continue (or type 'back' to return to menu): " INPUT
    check_back "$INPUT" && return 1
    return 0
  fi
  
  # Proceed with deletion
  printf "Deleting document ${BLUE}$DOC_ID${NC} from library ${BLUE}$LIB_ID${NC}...\n"
  
  RESPONSE=$(curl -s -X DELETE \
    "http://localhost:8000/libraries/$LIB_ID/documents/$DOC_ID" \
    -H "accept: application/json")
  
  if echo "$RESPONSE" | grep -q "\"status\":\"deleted\""; then
    printf "${GREEN}Document deleted successfully!${NC}\n"
    printf "${YELLOW}Note: Document ID has been cleared.${NC}\n"
    # Clear the document ID since it's now deleted
    DOC_ID=""
  else
    printf "${RED}Error deleting document:${NC}\n"
    echo "$RESPONSE" | jq
  fi
  
  read -p "Press Enter to continue (or type 'back' to return to menu): " INPUT
  check_back "$INPUT" && return 1
  return 0
}

delete_chunk() {
  show_header
  printf "${YELLOW}Delete a Chunk${NC}\n\n"
  
  # Check if library ID and document ID are set
  if [ -z "$LIB_ID" ]; then
    printf "${RED}Error: Library ID not set. Please set a library ID first.${NC}\n"
    read -p "Press Enter to continue (or type 'back' to return to menu): " INPUT
    check_back "$INPUT" && return 1
    return 0
  fi
  
  if [ -z "$DOC_ID" ]; then
    printf "${RED}Error: Document ID not set. Please set a document ID first.${NC}\n"
    read -p "Press Enter to continue (or type 'back' to return to menu): " INPUT
    check_back "$INPUT" && return 1
    return 0
  fi
  
  # Ask for chunk ID
  read -p "Enter Chunk ID (or type 'back' to return): " CHUNK_ID
  check_back "$CHUNK_ID" && return 1
  
  # Check current index status
  printf "Checking current index status...\n"
  INDEX_STATUS=$(curl -s "http://localhost:8000/libraries/$LIB_ID/index" | jq -r '.status')
  
  # Confirm deletion
  printf "${RED}WARNING: You are about to delete chunk $CHUNK_ID from document $DOC_ID!${NC}\n"
  printf "${YELLOW}The system will automatically handle incremental index updates.${NC}\n"
  
  read -p "Are you sure you want to proceed? (y/n): " DELETE_CONFIRM
  
  if [[ ! "$DELETE_CONFIRM" =~ ^[Yy]$ ]]; then
    printf "${YELLOW}Deletion cancelled.${NC}\n"
    read -p "Press Enter to continue (or type 'back' to return to menu): " INPUT
    check_back "$INPUT" && return 1
    return 0
  fi
  
  # Proceed with deletion
  printf "Deleting chunk ${BLUE}$CHUNK_ID${NC} from document ${BLUE}$DOC_ID${NC} in library ${BLUE}$LIB_ID${NC}...\n"
  
  RESPONSE=$(curl -s -X DELETE \
    "http://localhost:8000/libraries/$LIB_ID/documents/$DOC_ID/chunks/$CHUNK_ID" \
    -H "accept: application/json")
  
  if echo "$RESPONSE" | grep -q "\"status\":\"deleted\""; then
    printf "${GREEN}Chunk deleted successfully!${NC}\n"
    
    # Check index status after deletion
    AFTER_INDEX_STATUS=$(curl -s "http://localhost:8000/libraries/$LIB_ID/index" | jq -r '.status')
    
    if [ "$AFTER_INDEX_STATUS" = "current" ]; then
      printf "${GREEN}Index has been updated incrementally.${NC}\n"
    else
      printf "${YELLOW}Index status is now: $AFTER_INDEX_STATUS${NC}\n"
      printf "${YELLOW}The index will be automatically updated during the next search.${NC}\n"
    fi
  else
    printf "${RED}Error deleting chunk:${NC}\n"
    echo "$RESPONSE" | jq
  fi
  
  read -p "Press Enter to continue (or type 'back' to return to menu): " INPUT
  check_back "$INPUT" && return 1
  return 0
} 