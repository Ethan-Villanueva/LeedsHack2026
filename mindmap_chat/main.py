"""
Main entry point: Interactive CLI for the mindmap chat system.
"""

import sys
from config import config, validate_config
from llm.deepseek import DeepSeekClient  # Use DeepSeek for generation
from storage import JSONStorage
from conversation import ConversationManager


def print_help():
    """Print command help."""
    print("""
Commands:
  /new          Start a new conversation
  /map          View the mindmap
  /blocks       List all blocks
  /switch <id>  Switch to a block
  /clear        Clear conversation history
  /help         Show this help
  /exit         Exit
  
Just type to continue the current conversation.
""")


def main():
    """Main CLI loop."""
    try:
        validate_config()
    except ValueError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    
    # Initialize
    print("[INIT] Initializing Mindmap Chat (DeepSeek + Gemini Embeddings)...")
    llm = DeepSeekClient()
    storage = JSONStorage(config.storage_path)
    manager = ConversationManager(llm, storage)
    
    print("[OK] Ready!")
    print_help()
    
    # Main loop
    while True:
        try:
            user_input = input("\n> ").strip()
            
            if not user_input:
                continue
            
            # Handle commands
            if user_input.startswith("/"):
                cmd = user_input.split()[0]
                
                if cmd == "/help":
                    print_help()
                
                elif cmd == "/new":
                    print("Starting new conversation...")
                    first_msg = input("What do you want to discuss? > ").strip()
                    if first_msg:
                        response = manager.start_new_conversation(first_msg)
                        print(f"\nAssistant: {response}")
                
                elif cmd == "/map":
                    manager.print_mindmap()
                
                elif cmd == "/blocks":
                    graph_data = manager.export_graph()
                    print("\nBlocks:")
                    for block_id, block_data in graph_data["blocks"].items():
                        print(f"  {block_id}: {block_data['title']}")
                
                elif cmd == "/switch":
                    try:
                        block_id = user_input.split()[1]
                        summary = manager.switch_block(block_id)
                        print(summary)
                    except IndexError:
                        print("Usage: /switch <block_id>")
                
                elif cmd == "/clear":
                    storage.clear()
                    manager.graph = storage.load()
                    print("[OK] Cleared")
                
                elif cmd == "/exit":
                    print("Goodbye!")
                    break
                
                else:
                    print(f"Unknown command: {cmd}")
            
            else:
                # Regular conversation
                if not manager.graph.root_block_id:
                    # No conversation started yet
                    response = manager.start_new_conversation(user_input)
                else:
                    # Continue conversation
                    response = manager.continue_conversation(user_input)
                
                print(f"\nAssistant: {response}")
        
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
