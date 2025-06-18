from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet

class ActionExtractBudget(Action):
    def name(self) -> Text:
        return "action_extract_budget"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Get the last user message
        message = tracker.latest_message.get('text', '')
        
        # Try to extract a number from the message
        import re
        numbers = re.findall(r'\d+(?:k|thousand)?', message.lower())
        
        if numbers:
            # Take the first number found
            budget = numbers[0]
            # Convert k or thousand to full number
            if 'k' in budget:
                budget = str(int(budget.replace('k', '')) * 1000)
            elif 'thousand' in budget:
                budget = str(int(budget.replace('thousand', '')) * 1000)
            
            return [SlotSet("budget", budget)]
        
        return []