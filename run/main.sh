#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source "$SCRIPT_DIR/functions/utils.sh"
source "$SCRIPT_DIR/functions/dependencies.sh"

source "$SCRIPT_DIR/steps/create_library.sh"
source "$SCRIPT_DIR/steps/create_document.sh"
source "$SCRIPT_DIR/steps/add_chunks.sh"
source "$SCRIPT_DIR/steps/build_index.sh"
source "$SCRIPT_DIR/steps/search.sh"
source "$SCRIPT_DIR/steps/list_operations.sh"
source "$SCRIPT_DIR/steps/set_ids.sh"

main() {
  
  check_dependencies
  
  
  check_api_server
  
  while true; do
    show_header
    
    printf "${YELLOW}Welcome to VectorFlow Demo!${NC}\n\n"
    printf "Choose an option:\n"
    printf "1) Run Example Demo (Recommended for first-time users)\n"
    printf "2) Run Custom Steps\n"
    printf "h) Help - Show Instructions\n"
    printf "e) Exit\n\n"
    printf "${YELLOW}Tip: Type 'back' at any prompt to return to this menu${NC}\n\n"
    
    read -p "Enter your choice: " MAIN_CHOICE
    
    case $MAIN_CHOICE in
      1) 
        run_demo
        
        if [ $? -eq 0 ]; then
          show_custom_menu
        fi
        ;;
      2) 
        show_custom_menu
        ;;
      h|H|help) 
        show_help
        read -p "Press Enter to continue: " INPUT
        ;;
      e|E|exit) 
        show_header
        printf "${GREEN}Thank you for using VectorFlow!${NC}\n"
        exit 0
        ;;
      *) 
        printf "${RED}Invalid option. Please try again.${NC}\n" 
        read -p "Press Enter to continue: " INPUT
        ;;
    esac
  done
}

run_demo() {
  show_header
  printf "${GREEN}Starting the VectorFlow Demo...${NC}\n"
  printf "${YELLOW}Following the recommended flow of operations.${NC}\n"
  printf "${YELLOW}(You can type 'back' at any prompt to return to the main menu)${NC}\n\n"
  
  
  create_library
  if [ $? -eq 1 ]; then return 1; fi
  
  
  create_document
  if [ $? -eq 1 ]; then return 1; fi
  
  
  add_chunks
  if [ $? -eq 1 ]; then return 1; fi
  
  
  build_index
  if [ $? -eq 1 ]; then return 1; fi
  
  
  search
  if [ $? -eq 1 ]; then return 1; fi
  
  
  printf "\n${GREEN}Demo steps completed successfully!${NC}\n"
  printf "${YELLOW}You can now choose additional operations from the menu.${NC}\n"
  read -p "Press Enter to continue to menu: " INPUT
  
  return 0
}

show_custom_menu() {
  while true; do
    show_header
    
    printf "${YELLOW}Current Settings:${NC}\n"
    [ ! -z "$LIB_ID" ] && printf "Library ID: ${BLUE}$LIB_ID${NC}\n" || printf "Library ID: ${RED}Not set${NC}\n"
    [ ! -z "$DOC_ID" ] && printf "Document ID: ${BLUE}$DOC_ID${NC}\n" || printf "Document ID: ${RED}Not set${NC}\n"
    printf "\n"
  
    
    printf "${BLUE}VECTORFLOW DEMO - AVAILABLE STEPS:${NC}\n"
    printf "0) Set Library ID Manually\n"
    printf "00) Set Document ID Manually\n"
    printf "1) Create a Library\n"
    printf "2) Create a Document\n"
    printf "3) Add Chunks\n"
    printf "4) Build an Index\n"
    printf "5) Search\n"
    printf "7) List Documents\n"
    printf "8) List Libraries\n"
    printf "9) List Chunks\n"
    printf "b) Back to Main Menu\n"
    printf "h) Help\n"
    printf "e) Exit\n\n"
    printf "${YELLOW}(Type 'back' to return to main menu)${NC}\n"
    read -p "Choose a step (0-9, h, b, e) or 'exit' to quit: " CHOICE
    
    check_back "$CHOICE" && return 1
    
    
    case $CHOICE in
      0) set_library_id ;;
      00) set_document_id ;;
      1) create_library ;;
      2) create_document ;;
      3) add_chunks ;;
      4) build_index ;;
      5) search ;;
      7) list_documents ;;
      8) list_libraries ;;
      9) list_chunks ;;
      h|H|help) 
        show_help
        read -p "Press Enter to continue (or type 'back' to return to main menu): " INPUT
        check_back "$INPUT" && return 1
        ;;
      b|B) 
        return 1
        ;;  
      e|E|exit|EXIT|q|Q) 
        show_header
        printf "${GREEN}Thank you for using VectorFlow!${NC}\n"
        exit 0
        ;;
      *) 
        printf "${RED}Invalid choice. Please select a valid option.${NC}\n"
        read -p "Press Enter to continue (or type 'back' to return to main menu): " INPUT
        check_back "$INPUT" && return 1
        ;;
    esac
  done
}

main 