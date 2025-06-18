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
        
        # Remove any currency symbols and common words
        message = message.lower().replace('$', '').replace('usd', '').replace('dollars', '')
        
        # Look for different number formats
        # This will match:
        # - Simple numbers (10000)
        # - Numbers with k (10k, 10K)
        # - Numbers with thousand/k (10 thousand, 10thousand)
        # - Numbers with commas (10,000)
        patterns = [
            r'\b(\d+(?:,\d{3})*)\b',  # matches: 10000, 10,000
            r'\b(\d+)k\b',  # matches: 10k
            r'\b(\d+)\s*thousand\b',  # matches: 10 thousand
        ]
        
        budget = None
        for pattern in patterns:
            matches = re.findall(pattern, message, re.IGNORECASE)
            if matches:
                # Take the first match
                value = matches[0]
                # Remove commas if present
                value = value.replace(',', '')
                # Convert to integer
                try:
                    if 'k' in message or 'thousand' in message:
                        budget = str(int(value) * 1000)
                    else:
                        budget = str(int(value))
                    break
                except ValueError:
                    continue

        if budget:
            return [SlotSet("budget", budget)]
        else:
            dispatcher.utter_message(text="I'm having trouble understanding your budget. Please enter it as a number, like '20000' or '20k'.")
            return []

class ActionExtractFuelType(Action):
    def name(self) -> Text:
        return "action_extract_fuel_type"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Get the last user message
        message = tracker.latest_message.get('text', '').lower()
        
        # Define fuel type mappings
        fuel_mappings = {
            'gas': ['gas', 'gasoline', 'petrol'],
            'diesel': ['diesel'],
            'hybrid': ['hybrid'],
            'electric': ['electric', 'ev']
        }
        
        # Try to find a matching fuel type
        selected_fuel = None
        for fuel_type, variations in fuel_mappings.items():
            if any(var in message for var in variations):
                selected_fuel = fuel_type
                break
        
        if selected_fuel:
            return [SlotSet("fuel_type", selected_fuel)]
        else:
            dispatcher.utter_message(text="Could you please specify if you want gas, diesel, hybrid, or electric?")
            return []

class ActionGreetWithName(Action):
    def name(self) -> Text:
        return "action_greet_with_name"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Debug: Print the full message
        print(f"Full message: {tracker.latest_message}")
        
        # Get the extracted entities
        entities = tracker.latest_message.get('entities', [])
        
        # Debug: Print all entities
        print(f"Entities found: {entities}")
        
        # Get the intent
        intent = tracker.latest_message.get('intent', {}).get('name')
        print(f"Detected intent: {intent}")
        
        # Try to find name entity
        name = None
        for entity in entities:
            if entity['entity'] == 'name':
                name = entity['value']
                print(f"Found name entity: {name}")
                break
        
        if name:
            message = f"Hello {name}! I'm your car recommendation assistant. I can help you find the perfect car based on your needs. Shall we start?"
            print(f"Sending personalized message: {message}")
            dispatcher.utter_message(text=message)
            return [SlotSet("name", name)]
        else:
            print("No name found, using default greeting")
            dispatcher.utter_message(response="utter_greet")
            return []

class ActionSummarizeAndRecommend(Action):
    def name(self) -> Text:
        return "action_summarize_and_recommend"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Get all slot values
        purpose = tracker.get_slot("purpose")
        budget = tracker.get_slot("budget")
        fuel_type = tracker.get_slot("fuel_type")
        size = tracker.get_slot("size")

        # Debug print
        print(f"Slots - Purpose: {purpose}, Budget: {budget}, Fuel Type: {fuel_type}, Size: {size}")

        # Check if we have all required information
        if not all([purpose, budget, fuel_type]):
            missing_info = []
            if not purpose:
                missing_info.append("purpose")
            if not budget:
                missing_info.append("budget")
            if not fuel_type:
                missing_info.append("fuel type")
            
            dispatcher.utter_message(text=f"I'm missing some information: {', '.join(missing_info)}. Could you please provide these details?")
            return []

        # Create summary message with variations
        import random
        summary_templates = [
            f"Let me summarize your preferences: You want a {size if size else ''} car for {purpose}, with a budget of ${budget} and {fuel_type} fuel type. Here are my recommendations:",
            f"Based on your requirements: {size if size else ''} car for {purpose}, budget of ${budget}, and {fuel_type} fuel type. Here are some great options:",
            f"Perfect! I've got your preferences: {size if size else ''} car for {purpose}, ${budget} budget, and {fuel_type} fuel type. Here are my top recommendations:"
        ]
        
        summary = random.choice(summary_templates)
        
        # Debug print
        print(f"Sending summary: {summary}")
        dispatcher.utter_message(text=summary)
        
        # Convert budget to integer for comparison
        try:
            budget_int = int(budget)
        except ValueError:
            dispatcher.utter_message(text="I'm having trouble understanding your budget. Please try again with a clear number.")
            return []

        # Define car recommendations with prices and attributes
        car_recommendations = {
            "city_budget": [
                {"name": "Honda Civic", "price": 22550, "desc": "efficient, reliable", "size": "compact", "fuel": "gas"},
                {"name": "Toyota Corolla", "price": 21900, "desc": "excellent fuel economy, affordable", "size": "compact", "fuel": "gas"},
                {"name": "Hyundai Elantra", "price": 20950, "desc": "great value, modern features", "size": "compact", "fuel": "gas"},
                {"name": "Kia Forte", "price": 19890, "desc": "stylish, fuel-efficient", "size": "compact", "fuel": "gas"},
                {"name": "Mazda3", "price": 22550, "desc": "premium feel, good handling", "size": "compact", "fuel": "gas"},
                {"name": "Nissan Sentra", "price": 20510, "desc": "fuel-efficient, modern", "size": "compact", "fuel": "gas"},
                {"name": "Subaru Impreza", "price": 19755, "desc": "all-wheel drive, practical", "size": "compact", "fuel": "gas"},
                {"name": "Volkswagen Jetta", "price": 20655, "desc": "refined, efficient", "size": "compact", "fuel": "gas"},
                {"name": "Toyota Prius", "price": 24200, "desc": "hybrid, excellent mpg", "size": "compact", "fuel": "hybrid"},
                {"name": "Honda Insight", "price": 23900, "desc": "hybrid, spacious", "size": "compact", "fuel": "hybrid"},
                {"name": "Volkswagen Golf TDI", "price": 23400, "desc": "diesel efficiency, fun to drive", "size": "compact", "fuel": "diesel"},
                {"name": "Chevrolet Cruze Diesel", "price": 22800, "desc": "diesel economy, comfortable", "size": "compact", "fuel": "diesel"},
                {"name": "BMW 320d", "price": 42900, "desc": "luxury diesel, sporty", "size": "compact", "fuel": "diesel"},
                {"name": "Audi A3 TDI", "price": 35900, "desc": "premium diesel, refined", "size": "compact", "fuel": "diesel"},
                {"name": "Mercedes-Benz C220d", "price": 44900, "desc": "luxury diesel, comfortable", "size": "compact", "fuel": "diesel"}
            ],
            "family": [
                {"name": "Toyota RAV4", "price": 27950, "desc": "spacious SUV, reliable", "size": "SUV", "fuel": "gas"},
                {"name": "Honda CR-V", "price": 27400, "desc": "comfortable, good safety features", "size": "SUV", "fuel": "gas"},
                {"name": "Mazda CX-5", "price": 26700, "desc": "premium feel, good safety", "size": "SUV", "fuel": "gas"},
                {"name": "Subaru Forester", "price": 25195, "desc": "excellent visibility, all-wheel drive", "size": "SUV", "fuel": "gas"},
                {"name": "Kia Sorento", "price": 29390, "desc": "three-row option, good value", "size": "SUV", "fuel": "gas"},
                {"name": "Volkswagen Tiguan", "price": 26490, "desc": "versatile, good cargo space", "size": "SUV", "fuel": "gas"},
                {"name": "Hyundai Tucson", "price": 24950, "desc": "modern tech, comfortable ride", "size": "SUV", "fuel": "gas"},
                {"name": "Ford Escape", "price": 26760, "desc": "efficient, good handling", "size": "SUV", "fuel": "gas"},
                {"name": "Nissan Rogue", "price": 26700, "desc": "spacious, good value", "size": "SUV", "fuel": "gas"},
                {"name": "Chevrolet Equinox", "price": 26600, "desc": "fuel-efficient, practical", "size": "SUV", "fuel": "gas"},
                {"name": "Volkswagen Touareg TDI", "price": 48900, "desc": "luxury diesel SUV, powerful", "size": "SUV", "fuel": "diesel"},
                {"name": "BMW X5 xDrive30d", "price": 62900, "desc": "premium diesel SUV, sporty", "size": "SUV", "fuel": "diesel"},
                {"name": "Mercedes-Benz GLE 300d", "price": 58900, "desc": "luxury diesel SUV, comfortable", "size": "SUV", "fuel": "diesel"},
                {"name": "Audi Q7 TDI", "price": 56900, "desc": "premium diesel SUV, spacious", "size": "SUV", "fuel": "diesel"},
                {"name": "Land Rover Discovery Sport", "price": 45900, "desc": "capable diesel SUV, versatile", "size": "SUV", "fuel": "diesel"},
                {"name": "Jeep Grand Cherokee EcoDiesel", "price": 42900, "desc": "rugged diesel SUV, powerful", "size": "SUV", "fuel": "diesel"},
                {"name": "Toyota Highlander Hybrid", "price": 36620, "desc": "hybrid SUV, efficient", "size": "SUV", "fuel": "hybrid"},
                {"name": "Lexus RX 450h", "price": 46900, "desc": "luxury hybrid SUV, refined", "size": "SUV", "fuel": "hybrid"},
                {"name": "Ford Explorer Hybrid", "price": 38900, "desc": "spacious hybrid SUV, practical", "size": "SUV", "fuel": "hybrid"},
                {"name": "Acura MDX Hybrid", "price": 42900, "desc": "premium hybrid SUV, comfortable", "size": "SUV", "fuel": "hybrid"},
                {"name": "Volvo XC90 Recharge", "price": 54900, "desc": "plug-in hybrid SUV, luxurious", "size": "SUV", "fuel": "hybrid"}
            ],
            "electric": [
                {"name": "Tesla Model 3", "price": 38990, "desc": "long range, high tech", "size": "midsize", "fuel": "electric"},
                {"name": "Chevrolet Bolt", "price": 26500, "desc": "affordable, good range", "size": "compact", "fuel": "electric"},
                {"name": "Hyundai Kona Electric", "price": 33550, "desc": "practical, good value", "size": "compact", "fuel": "electric"},
                {"name": "Ford Mustang Mach-E", "price": 42995, "desc": "performance, style", "size": "SUV", "fuel": "electric"},
                {"name": "Volkswagen ID.4", "price": 38995, "desc": "spacious, good range", "size": "SUV", "fuel": "electric"},
                {"name": "Nissan Leaf", "price": 28140, "desc": "practical, proven reliability", "size": "compact", "fuel": "electric"},
                {"name": "Kia Niro EV", "price": 39550, "desc": "efficient, good range", "size": "compact", "fuel": "electric"},
                {"name": "Polestar 2", "price": 48400, "desc": "premium, innovative", "size": "midsize", "fuel": "electric"},
                {"name": "Mini Cooper SE", "price": 30900, "desc": "fun to drive, compact", "size": "compact", "fuel": "electric"},
                {"name": "Mazda MX-30", "price": 33470, "desc": "stylish, efficient", "size": "compact", "fuel": "electric"},
                {"name": "Tesla Model Y", "price": 43990, "desc": "electric SUV, long range", "size": "SUV", "fuel": "electric"},
                {"name": "Audi e-tron", "price": 66900, "desc": "luxury electric SUV", "size": "SUV", "fuel": "electric"},
                {"name": "Jaguar I-Pace", "price": 69900, "desc": "performance electric SUV", "size": "SUV", "fuel": "electric"},
                {"name": "Mercedes-Benz EQC", "price": 67900, "desc": "luxury electric SUV", "size": "SUV", "fuel": "electric"},
                {"name": "BMW iX", "price": 84900, "desc": "premium electric SUV", "size": "SUV", "fuel": "electric"}
            ]
        }

        # Combine all cars into one list for filtering
        all_cars = []
        for category in car_recommendations.values():
            all_cars.extend(category)

        # Filter cars based on all criteria
        filtered_cars = []
        for car in all_cars:
            # Check if car matches all criteria
            matches_fuel = car["fuel"].lower() == fuel_type.lower()
            matches_size = not size or car["size"].lower() == size.lower()
            
            # More flexible budget matching
            # For SUVs and family cars, allow up to 50% over budget
            # For other cars, stick to budget
            budget_multiplier = 1.5 if (size and size.lower() == "suv") or (purpose and "family" in purpose.lower()) else 1.0
            matches_budget = car["price"] <= (budget_int * budget_multiplier)
            
            # For purpose, we need to be more flexible
            matches_purpose = True
            if purpose:
                purpose_lower = purpose.lower()
                if "family" in purpose_lower and car["size"].lower() != "suv":
                    matches_purpose = False
                elif "city" in purpose_lower and car["size"].lower() not in ["compact", "midsize"]:
                    matches_purpose = False
                elif "long" in purpose_lower and car["size"].lower() not in ["midsize", "suv"]:
                    matches_purpose = False

            if matches_fuel and matches_size and matches_budget and matches_purpose:
                filtered_cars.append(car)

        # Sort by how close they are to the budget
        filtered_cars.sort(key=lambda x: abs(x["price"] - budget_int))
        
        if not filtered_cars:
            dispatcher.utter_message(text=f"I apologize, but I couldn't find any cars matching all your criteria. Would you like to try adjusting some of your preferences?")
            return []

        # Store the remaining cars in a slot for later use
        remaining_cars = filtered_cars[5:] if len(filtered_cars) > 5 else []
        
        # Format the first 5 recommendations
        recommendations = "Based on your requirements, I recommend:\n"
        for car in filtered_cars[:5]:
            recommendations += f"- {car['name']} (starting at ${car['price']:,}, {car['desc']})\n"

        # Add a note about budget flexibility if needed
        if size and size.lower() == "suv" and budget_int < 25000:
            recommendations += "\nNote: Most SUVs start above $25,000. You might want to consider increasing your budget or looking at compact SUVs for better value."

        dispatcher.utter_message(text=recommendations)
        
        # If there are more cars available, ask if they want to see more
        if remaining_cars:
            dispatcher.utter_message(text="Would you like to see more recommendations?")
            # Store the remaining cars as a list of dictionaries
            return [SlotSet("remaining_cars", [{"name": car["name"], "price": car["price"], "desc": car["desc"]} for car in remaining_cars])]
        
        return []

class ActionExtractCarSize(Action):
    def name(self) -> Text:
        return "action_extract_car_size"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Get the last user message
        message = tracker.latest_message.get('text', '').lower()
        
        # First check for entities
        entities = tracker.latest_message.get('entities', [])
        for entity in entities:
            if entity['entity'] == 'size':
                size_value = entity['value'].lower()
                # Normalize SUV value
                if size_value in ['suv', 'crossover']:
                    size_value = 'SUV'
                return [SlotSet("size", size_value)]
        
        # If no entity found, try pattern matching
        size_mappings = {
            'compact': ['compact', 'small'],
            'midsize': ['midsize', 'mid-size', 'mid size', 'medium'],
            'SUV': ['suv', 'crossover', 'sport utility vehicle'],
            'full-size': ['full-size', 'full size', 'large', 'fullsize'],
            'truck': ['truck', 'pickup']
        }
        
        # Try to find a matching car size
        selected_size = None
        for size_type, variations in size_mappings.items():
            if any(var in message for var in variations):
                selected_size = size_type
                break
        
        if selected_size:
            # Debug print
            print(f"Extracted car size: {selected_size}")
            return [SlotSet("size", selected_size)]
        else:
            dispatcher.utter_message(text="Could you please specify if you want a compact, midsize, SUV, full-size car, or truck?")
            return []

class ActionShowMoreCars(Action):
    def name(self) -> Text:
        return "action_show_more_cars"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Get the remaining cars from the slot
        remaining_cars = tracker.get_slot("remaining_cars")
        
        if not remaining_cars:
            dispatcher.utter_message(text="I don't have any more recommendations at the moment.")
            return []
        
        # Format the next 5 recommendations
        recommendations = "Here are more options that match your criteria:\n"
        for car in remaining_cars[:5]:
            recommendations += f"- {car['name']} (starting at ${car['price']:,}, {car['desc']})\n"
        
        dispatcher.utter_message(text=recommendations)
        
        # Update remaining cars
        new_remaining = remaining_cars[5:] if len(remaining_cars) > 5 else []
        
        if new_remaining:
            dispatcher.utter_message(text="Would you like to see more recommendations?")
            return [SlotSet("remaining_cars", new_remaining)]
        else:
            dispatcher.utter_message(text="That's all the recommendations I have for now.")
            return [SlotSet("remaining_cars", None)]
