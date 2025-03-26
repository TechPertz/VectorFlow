#!/bin/bash

add_chunks() {
  if [ -z "$LIB_ID" ] || [ -z "$DOC_ID" ]; then
    printf "${RED}Error: You need to create a library and document first (Steps 1-2)${NC}\n"
    read -p "Press Enter to continue (or type 'back'): " INPUT
    check_back "$INPUT" && return 1
    return 0
  fi

  printf "\n${BLUE}STEP 3: Adding text chunks with embeddings${NC}\n"
  printf "Choose how to create vector embeddings for your text chunks:\n"
  printf "  1. Use sample texts with Cohere API for embeddings\n"
  printf "  2. Enter your own text and use Cohere API for embeddings\n"
  printf "${YELLOW}To return to the main menu, type 'back' and press Enter.${NC}\n\n"
  read -p "Enter your choice (1-2) [1] (or type 'back'): " INPUT
  
  
  if [ -z "$INPUT" ]; then
    INPUT="1"
  fi
  
  
  check_back "$INPUT" && return 1
  
  
  if [ "$INPUT" != "1" ] && [ "$INPUT" != "2" ]; then
    printf "${RED}Invalid choice. Using default: 1${NC}\n"
    INPUT="1"
  fi
  
  EMBEDDING_CHOICE="$INPUT"

  if [ "$EMBEDDING_CHOICE" -eq 1 ]; then
    printf "${GREEN}Adding chunks using Cohere batch embeddings API...${NC}\n"
    
    
    curl -L -s -X POST "http://localhost:8000/libraries/$LIB_ID/batch-chunks" \
      -H "Content-Type: application/json" \
      -d '{
        "texts": [
          "Attention mechanisms revolutionized natural language processing by enabling models to focus on relevant parts of the input",
          "The transformer architecture introduced in 2017 has become the foundation for most state-of-the-art NLP models",
          "BERT (Bidirectional Encoder Representations from Transformers) improved language understanding by considering context in both directions",
          "GPT (Generative Pre-trained Transformer) models excel at text generation by predicting the next token in a sequence",
          "Transfer learning in NLP involves pre-training on large corpora and fine-tuning on specific tasks",
          "Tokenization is the process of converting text into smaller units that can be processed by neural networks",
          "Embeddings represent words or tokens as dense vectors in a continuous vector space",
          "Attention scores determine how much focus to place on different input tokens when generating an output",
          "Self-attention allows tokens to attend to all other tokens in the same sequence, capturing long-range dependencies",
          "The transformer encoder-decoder architecture forms the basis for machine translation and other sequence-to-sequence tasks"
        ],
        "metadata": [
          {"name": "attention_mechanism"},
          {"name": "transformer_overview"},
          {"name": "bert_model"},
          {"name": "gpt_model"},
          {"name": "transfer_learning"},
          {"name": "tokenization"},
          {"name": "embeddings"},
          {"name": "attention_scores"},
          {"name": "self_attention"},
          {"name": "encoder_decoder"}
        ],
        "document_id": "'"$DOC_ID"'"
      }' > /dev/null
    printf "${GREEN}Added 10 chunks with Cohere-generated embeddings.${NC}\n"
  else
    
    printf "${GREEN}Enter your own text and generate embeddings with Cohere API...${NC}\n"
    printf "${YELLOW}Enter one paragraph per chunk. Press Enter after each chunk.${NC}\n"
    printf "${YELLOW}To finish entering chunks, press Enter twice on an empty line.${NC}\n\n"
    
    
    TEXTS=()
    METADATA=()
    COUNT=1
    
    while true; do
      printf "${BLUE}Chunk ${COUNT}:${NC}\n"
      printf "Enter text (or press Enter twice to finish): \n"
      
      
      read -r TEXT
      
      
      if [ -z "$TEXT" ]; then
        printf "${YELLOW}No text entered. Do you want to submit all chunks?${NC}\n"
        read -p "Submit all chunks now? (y/n) [y]: " SUBMIT
        SUBMIT=${SUBMIT:-y}
        
        if [[ "$SUBMIT" == "y" || "$SUBMIT" == "Y" ]]; then
          break
        else
          continue
        fi
      fi
      
      
      read -p "Enter a name/label for this chunk: " CHUNK_NAME
      if [ -z "$CHUNK_NAME" ]; then
        CHUNK_NAME="chunk_$COUNT"
      fi
      
      
      TEXTS+=("$TEXT")
      METADATA+=("{\"name\": \"$CHUNK_NAME\"}")
      
      ((COUNT++))
      printf "\n"
    done
    
    
    if [ ${#TEXTS[@]} -eq 0 ]; then
      printf "${RED}No text chunks were provided. Operation cancelled.${NC}\n"
    else
      
      printf "${GREEN}Preparing data for ${#TEXTS[@]} chunks...${NC}\n"
      
      
      JSON_TEXTS="["
      for i in "${!TEXTS[@]}"; do
        
        ESCAPED_TEXT=$(echo "${TEXTS[$i]}" | sed 's/"/\\"/g')
        JSON_TEXTS+="\"$ESCAPED_TEXT\""
        if [ $i -lt $((${#TEXTS[@]} - 1)) ]; then
          JSON_TEXTS+=","
        fi
      done
      JSON_TEXTS+="]"
      
      
      JSON_METADATA="["
      for i in "${!METADATA[@]}"; do
        JSON_METADATA+="${METADATA[$i]}"
        if [ $i -lt $((${#METADATA[@]} - 1)) ]; then
          JSON_METADATA+=","
        fi
      done
      JSON_METADATA+="]"
      
      
      JSON_PAYLOAD="{\"texts\": $JSON_TEXTS, \"metadata\": $JSON_METADATA, \"document_id\": \"$DOC_ID\"}"
      
      printf "${GREEN}Sending ${#TEXTS[@]} chunks to API...${NC}\n"
      RESPONSE=$(curl -L -s -w "\n%{http_code}" -X POST "http://localhost:8000/libraries/$LIB_ID/batch-chunks" \
        -H "Content-Type: application/json" \
        -d "$JSON_PAYLOAD")
      
      HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
      BODY=$(echo "$RESPONSE" | sed '$d')
      
      if [ "$HTTP_CODE" -eq 201 ] || [ "$HTTP_CODE" -eq 200 ]; then
        printf "${GREEN}Successfully added ${#TEXTS[@]} chunks with embeddings.${NC}\n"
      else
        ERROR_MSG=$(echo "$BODY" | jq -r .detail 2>/dev/null || echo "Unknown error")
        printf "${RED}Error adding chunks: $ERROR_MSG (HTTP $HTTP_CODE)${NC}\n"
      fi
    fi
  fi
  
  read -p "Press Enter to continue (or type 'back'): " INPUT
  check_back "$INPUT" && return 1
  
  return 0
} 