"""
Bishop Bot - Game Rules Manager
Last updated: 2025-05-31 18:33:27 UTC by Bioku87
"""
import os
import json
import logging
import re
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger('bishop_bot.rules')

class RulesManager:
    """Manages game rules lookup and reference"""
    
    def __init__(self):
        """Initialize the rules manager"""
        self.rules_data = {}
        self.loaded_systems = []
        
        # Load available rule systems
        self.load_available_systems()
        
        logger.info("Rules manager initialized")
    
    def load_available_systems(self):
        """Load available rule systems from data directory"""
        try:
            rules_dir = "data/game/rules"
            os.makedirs(rules_dir, exist_ok=True)
            
            # Check for rule system directories
            for system_dir in os.listdir(rules_dir):
                system_path = os.path.join(rules_dir, system_dir)
                if os.path.isdir(system_path):
                    # Check for index.json file
                    index_path = os.path.join(system_path, "index.json")
                    if os.path.isfile(index_path):
                        self.loaded_systems.append(system_dir)
            
            logger.info(f"Available rule systems: {', '.join(self.loaded_systems)}")
        except Exception as e:
            logger.error(f"Error loading rule systems: {e}")
    
    def load_system(self, system_name: str) -> bool:
        """Load a specific rule system"""
        try:
            if system_name in self.rules_data:
                # Already loaded
                return True
            
            rules_dir = os.path.join("data/game/rules", system_name)
            if not os.path.isdir(rules_dir):
                logger.error(f"Rule system directory not found: {rules_dir}")
                return False
            
            # Load index.json
            index_path = os.path.join(rules_dir, "index.json")
            if not os.path.isfile(index_path):
                logger.error(f"Rule system index not found: {index_path}")
                return False
            
            with open(index_path, 'r', encoding='utf-8') as f:
                index = json.load(f)
            
            # Load each rules file
            rules_data = {
                "meta": index.get("meta", {}),
                "categories": {}
            }
            
            for category, file_info in index.get("files", {}).items():
                filename = file_info.get("filename")
                if not filename:
                    continue
                
                file_path = os.path.join(rules_dir, filename)
                if not os.path.isfile(file_path):
                    logger.warning(f"Rules file not found: {file_path}")
                    continue
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    category_data = json.load(f)
                
                rules_data["categories"][category] = category_data
            
            self.rules_data[system_name] = rules_data
            logger.info(f"Loaded rule system: {system_name}")
            
            return True
        except Exception as e:
            logger.error(f"Error loading rule system {system_name}: {e}")
            return False
    
    def get_rule_categories(self, system_name: str) -> List[str]:
        """Get available rule categories for a system"""
        if system_name not in self.rules_data:
            if not self.load_system(system_name):
                return []
        
        return list(self.rules_data[system_name]["categories"].keys())
    
    def get_rule(self, system_name: str, category: str, rule_name: str) -> Optional[Dict[str, Any]]:
        """Get a specific rule"""
        if system_name not in self.rules_data:
            if not self.load_system(system_name):
                return None
        
        categories = self.rules_data[system_name]["categories"]
        if category not in categories:
            return None
        
        category_data = categories[category]
        for rule in category_data:
            if rule.get("name", "").lower() == rule_name.lower():
                return rule
        
        return None
    
    def search_rules(self, system_name: str, query: str) -> List[Dict[str, Any]]:
        """Search for rules matching the query"""
        if system_name not in self.rules_data:
            if not self.load_system(system_name):
                return []
        
        results = []
        query = query.lower()
        
        for category, category_data in self.rules_data[system_name]["categories"].items():
            for rule in category_data:
                rule_name = rule.get("name", "").lower()
                rule_desc = rule.get("description", "").lower()
                
                if query in rule_name or query in rule_desc:
                    # Add category to the rule for context
                    rule_copy = rule.copy()
                    rule_copy["category"] = category
                    results.append(rule_copy)
        
        return results
    
    def get_available_systems(self) -> List[str]:
        """Get a list of available rule systems"""
        return self.loaded_systems
    
    def create_default_rules(self):
        """Create default rules files"""
        # Create default rule system structure for D&D 5e
        system_name = "dnd5e"
        rules_dir = os.path.join("data/game/rules", system_name)
        os.makedirs(rules_dir, exist_ok=True)
        
        # Create index.json
        index = {
            "meta": {
                "name": "Dungeons & Dragons 5th Edition",
                "short_name": "D&D 5e",
                "version": "Basic Rules",
                "description": "Basic rules for D&D 5th Edition"
            },
            "files": {
                "abilities": {
                    "filename": "abilities.json",
                    "title": "Abilities and Skills"
                },
                "combat": {
                    "filename": "combat.json",
                    "title": "Combat Rules"
                },
                "conditions": {
                    "filename": "conditions.json",
                    "title": "Conditions"
                }
            }
        }
        
        with open(os.path.join(rules_dir, "index.json"), 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2)
        
        # Create abilities.json
        abilities = [
            {
                "name": "Strength",
                "abbreviation": "STR",
                "description": "Strength measures bodily power, athletic training, and the extent to which you can exert raw physical force.",
                "skills": ["Athletics"],
                "checks": [
                    "Forcing open a stuck, locked, or barred door",
                    "Breaking free of bonds",
                    "Pushing through a tunnel that is too small",
                    "Hanging on to a wagon while being dragged behind it",
                    "Tipping over a statue"
                ]
            },
            {
                "name": "Dexterity",
                "abbreviation": "DEX",
                "description": "Dexterity measures agility, reflexes, and balance.",
                "skills": ["Acrobatics", "Sleight of Hand", "Stealth"],
                "checks": [
                    "Moving along a narrow or slippery surface",
                    "Steering a chariot around a tight turn",
                    "Picking a lock",
                    "Disabling a trap",
                    "Securely tying up a prisoner"
                ]
            },
            {
                "name": "Constitution",
                "abbreviation": "CON",
                "description": "Constitution measures health, stamina, and vital force.",
                "skills": [],
                "checks": [
                    "Holding your breath",
                    "Marching or laboring for hours without rest",
                    "Going without sleep",
                    "Surviving without food or water",
                    "Resisting the effects of poison"
                ]
            }
        ]
        
        with open(os.path.join(rules_dir, "abilities.json"), 'w', encoding='utf-8') as f:
            json.dump(abilities, f, indent=2)
        
        # Create conditions.json
        conditions = [
            {
                "name": "Blinded",
                "description": "A blinded creature can't see and automatically fails any ability check that requires sight. Attack rolls against the creature have advantage, and the creature's attack rolls have disadvantage."
            },
            {
                "name": "Charmed",
                "description": "A charmed creature can't attack the charmer or target the charmer with harmful abilities or magical effects. The charmer has advantage on any ability check to interact socially with the creature."
            },
            {
                "name": "Deafened",
                "description": "A deafened creature can't hear and automatically fails any ability check that requires hearing."
            }
        ]
        
        with open(os.path.join(rules_dir, "conditions.json"), 'w', encoding='utf-8') as f:
            json.dump(conditions, f, indent=2)
        
        # Create combat.json
        combat = [
            {
                "name": "Attack Roll",
                "description": "When you make an attack roll, you roll a d20 and add your attack bonus. If the total equals or exceeds the target's Armor Class (AC), the attack hits."
            },
            {
                "name": "Critical Hit",
                "description": "When you roll a 20 on an attack roll, you score a critical hit. You roll damage dice twice and add relevant modifiers."
            },
            {
                "name": "Advantage and Disadvantage",
                "description": "Advantage: Roll two d20s and take the higher roll. Disadvantage: Roll two d20s and take the lower roll."
            }
        ]
        
        with open(os.path.join(rules_dir, "combat.json"), 'w', encoding='utf-8') as f:
            json.dump(combat, f, indent=2)
        
        logger.info(f"Created default rules for {system_name}")
        
        # Update loaded systems
        self.loaded_systems.append(system_name)