#!/bin/bash

build_index() {
  if [ -z "$LIB_ID" ]; then
    printf "${RED}Error: You need to create a library first (Step 1)${NC}\n"
    read -p "Press Enter to continue (or type 'back'): " INPUT
    check_back "$INPUT" && return 1
    return 0
  fi

  printf "\n${BLUE}STEP 4: Building a vector index${NC}\n"
  printf "Choose an indexing algorithm for similarity search:\n"
  printf "  1. kd_tree - KD-Tree (balanced spatial partitioning)\n"
  printf "  2. linear - Linear scan (brute force, accurate but slower)\n" 
  printf "  3. lsh - Locality Sensitive Hashing (approximate nearest neighbors)\n"
  printf "${YELLOW}To return to the main menu, type 'back' and press Enter.${NC}\n\n"
  read -p "Select an index type (1-3) [1] (or type 'back'): " INPUT
  
  
  if [ -z "$INPUT" ]; then
    INPUT="1"
  fi
  
  
  check_back "$INPUT" && return 1
  
  
  if [ "$INPUT" != "1" ] && [ "$INPUT" != "2" ] && [ "$INPUT" != "3" ]; then
    printf "${RED}Invalid choice. Using default: 1 (kd_tree)${NC}\n"
    INPUT="1"
  fi
  
  INDEX_CHOICE="$INPUT"

  case $INDEX_CHOICE in
    1) ALGORITHM="kd_tree" ;;
    2) ALGORITHM="linear" ;;
    3) ALGORITHM="lsh" ;;
    *) ALGORITHM="kd_tree" ;;
  esac

  printf "${GREEN}Building index with $ALGORITHM algorithm...${NC}\n"
  curl -L -s -X POST "http://localhost:8000/libraries/$LIB_ID/index?algorithm=$ALGORITHM" > /dev/null
  printf "${GREEN}Index built successfully.${NC}\n"
  
  read -p "Press Enter to continue (or type 'back'): " INPUT
  check_back "$INPUT" && return 1
  
  return 0
} 