#!/bin/bash
edit_provider_desc() {
    local provider_name="$1"
    local temp_file="/tmp/provider_edit.txt"
    
    if [ -z "$provider_name" ]; then
        echo "Usage: edit_provider_desc 'provider_name'"
        return 1
    fi
    
    echo "📋 Fetching current description for: $provider_name"
    psql -d directory -t -c "SELECT ai_description FROM providers WHERE provider_name ILIKE '%$provider_name%';" > "$temp_file"
    
    if [ ! -s "$temp_file" ]; then
        echo "❌ Provider not found or no description exists"
        rm "$temp_file"
        return 1
    fi
    
    echo "✏️ Opening in nano... (Ctrl+O to save, Ctrl+X to exit)"
    nano "$temp_file"
    
    echo "💾 Updating database..."
    local new_desc=$(cat "$temp_file" | sed "s/'/''/g")
    psql -d directory -c "UPDATE providers SET ai_description = '$new_desc' WHERE provider_name ILIKE '%$provider_name%';"
    
    echo "🔄 Syncing to WordPress..."
    python3 wordpress_sync_manager.py --sync-provider "$provider_name"
    
    rm "$temp_file"
    echo "✅ Done! Description updated and synced."
}

# Make function available
edit_provider_desc "$@"
