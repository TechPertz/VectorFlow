#!/bin/bash

set_library_id() {
  printf "\n${BLUE}Setting Library ID Manually${NC}\n"
  printf "This allows you to work with an existing library.\n"
  printf "${YELLOW}To return to the main menu, type 'back' and press Enter.${NC}\n\n"
  read -p "Enter the library ID (or type 'back'): " INPUT
  
  check_back "$INPUT" && return 1
  
  if [ -z "$INPUT" ]; then
    printf "${RED}Error: Library ID cannot be empty${NC}\n"
  else
    LIB_ID=$INPUT
    printf "${GREEN}Library ID set to: $LIB_ID${NC}\n"
    DOC_ID="" 
  fi
  
  read -p "Press Enter to continue (or type 'back'): " INPUT
  check_back "$INPUT" && return 1
  
  return 0
}

set_document_id() {
  if [ -z "$LIB_ID" ]; then
    printf "${RED}Error: You need to set or create a library first (Step 0 or 1)${NC}\n"
    read -p "Press Enter to continue (or type 'back'): " INPUT
    check_back "$INPUT" && return 1
    return 0
  fi

  printf "\n${BLUE}Setting Document ID Manually${NC}\n"
  printf "This allows you to work with an existing document in library $LIB_ID.\n"
  printf "${YELLOW}To return to the main menu, type 'back' and press Enter.${NC}\n\n"
  read -p "Enter the document ID (or type 'back'): " INPUT
  
  check_back "$INPUT" && return 1
  
  if [ -z "$INPUT" ]; then
    printf "${RED}Error: Document ID cannot be empty${NC}\n"
  else
    DOC_ID=$INPUT
    printf "${GREEN}Document ID set to: $DOC_ID${NC}\n"
  fi
  
  read -p "Press Enter to continue (or type 'back'): " INPUT
  check_back "$INPUT" && return 1
  
  return 0
} 