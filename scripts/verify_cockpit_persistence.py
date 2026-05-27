import json
from cockpit.app.app_foundation import CockpitState
from core.storage.storage_manager import storage_manager

def verify():
    state = CockpitState()
    test_chat = "chat_123"
    messages = [{"role": "user", "content": "hello"}]

    print(f"Saving test chat: {test_chat}")
    state.save_chat(test_chat, messages)

    # Reload state
    new_state = CockpitState()
    new_state.load_state()

    found = False
    for chat in new_state.active_chats:
        if chat["chat_id"] == test_chat:
            found = True
            print("Chat found in persisted state.")
            break

    if found:
        print("Persistence VERIFIED.")
    else:
        print("Persistence FAILED.")
        exit(1)

if __name__ == "__main__":
    verify()
