"""
Utility module for parsing the top_followup_threads.md file and converting to structured task format
"""
import re
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime


def parse_followup_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Parse the top_followup_threads.md file and return a list of structured task dictionaries.
    
    Args:
        file_path: Path to the markdown file
        
    Returns:
        List of task dictionaries in the frontend-compatible format
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Follow-up file not found: {file_path}")
    
    content = file_path.read_text(encoding='utf-8')
    lines = content.splitlines()
    
    tasks = []
    current_item = None
    
    # Regular expression to match task headers like "1. **Chat** · **Title** · 🔥9/10"
    task_header_pattern = re.compile(r'(\d+)\.\s*\*\*(.+?)\*\*\s*·\s*\*\*(.+?)\*\*\s*·\s*(.+)')

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Check for task header pattern
        task_match = task_header_pattern.match(line)
        if task_match:
            if current_item:  # Save previous item if exists
                tasks.append(current_item)
            
            # Extract task data
            index = int(task_match.group(1))
            chat_name = task_match.group(2).strip()
            title = task_match.group(3).strip()
            urgency = task_match.group(4).strip()
            
            current_item = {
                'id': index,
                'index': index,
                'chat_name': chat_name,
                'title': title,
                'urgency': urgency,
                'owner': '',
                'due_date': '',
                'jid': '',
                'next_step': '',
                'nudge': '',
                'source': '',
                'confidence': 0
            }
        
        # Parse details for current item
        elif current_item:
            # Owner line: **Owner:** @Rakesh · **Due:** Next business day 6 PM IST · **JID:** ...
            if '**Owner:**' in line and '· **Due:**' in line:
                owner_match = re.search(r'\*\*Owner:\*\*\s*(.*?)\s*·', line)
                due_match = re.search(r'·\s*\*\*Due:\*\*\s*(.*?)\s*·', line)
                jid_match = re.search(r'·\s*\*\*JID:\*\*\s*(.*)', line)
                
                if owner_match:
                    current_item['owner'] = owner_match.group(1).strip()
                if due_match:
                    current_item['due_date'] = due_match.group(1).strip()
                if jid_match:
                    current_item['jid'] = jid_match.group(1).strip()
            
            # Next step line: **Next step:** Connect with the NPCI team directly after Wednesday for an update.
            elif '**Next step:**' in line:
                next_step = line.replace('**Next step:**', '').strip()
                current_item['next_step'] = next_step
            
            # Nudge line: **Nudge:** "Rakesh, please connect with the NPCI team..."
            elif '**Nudge:**' in line:
                # Extract text between quotes
                nudge_match = re.search(r'"(.+)"', line)
                if nudge_match:
                    current_item['nudge'] = nudge_match.group(1).strip()
            
            # Source and confidence line: **Source:** 2025-11-03 11:57:39+05:30 | **Confidence:** 95%
            elif '**Source:**' in line and '| **Confidence:**' in line:
                source_match = re.search(r'\*\*Source:\*\*\s*(.*?)\s*\|', line)
                confidence_match = re.search(r'\|\s*\*\*Confidence:\*\*\s*(\d+)%', line)
                
                if source_match:
                    current_item['source'] = source_match.group(1).strip()
                if confidence_match:
                    try:
                        current_item['confidence'] = int(confidence_match.group(1))
                    except ValueError:
                        current_item['confidence'] = 0
        
        i += 1
    
    # Add the last item if it exists
    if current_item:
        tasks.append(current_item)
    
    return tasks


def get_task_stats(tasks: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Calculate task statistics from the loaded tasks.
    
    Args:
        tasks: List of task dictionaries
        
    Returns:
        Dictionary with total, completed, and remaining counts
    """
    total_tasks = len(tasks)
    # For now, all tasks are "pending" from a user perspective until interacted with
    # In a more sophisticated system, this would come from the database
    completed_tasks = 0
    remaining_tasks = total_tasks
    
    return {
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'remaining_tasks': remaining_tasks
    }


def markdown_to_task_format(item_index: int, markdown_item: str) -> Dict[str, Any]:
    """
    Convert a single markdown item string to the frontend task format.
    This is a helper function if needed later.
    
    Args:
        item_index: Index of the item in the list
        markdown_item: Single markdown item as string
        
    Returns:
        Dictionary in the frontend-compatible format
    """
    # Implementation would be similar to the main parser but for a single item
    # Currently not used since the main parser handles this
    pass


# Test the parser
if __name__ == "__main__":
    try:
        tasks = parse_followup_file("../wa_productivity/top_followup_threads.md")
        print(f"Parsed {len(tasks)} tasks")
        if tasks:
            print(f"First task: {tasks[0]}")
    except FileNotFoundError as e:
        print(f"Error: {e}")