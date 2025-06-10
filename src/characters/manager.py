"""
Bishop Bot - Character Manager
Last updated: 2025-05-31 18:16:31 UTC by Bioku87
"""
import os
import json
import logging
import discord
from typing import Dict, List, Any, Optional, Union
from database.manager import DatabaseManager

logger = logging.getLogger('bishop_bot.characters')

class Character:
    """Represents a character in the system"""
    
    def __init__(self, **kwargs):
        # Basic info
        self.id = kwargs.get('id')
        self.name = kwargs.get('name', 'Unnamed Character')
        self.player_id = kwargs.get('player_id')
        self.guild_id = kwargs.get('guild_id')
        
        # Character details
        self.character_class = kwargs.get('character_class', '')
        self.level = kwargs.get('level', 1)
        self.race = kwargs.get('race', '')
        self.background = kwargs.get('background', '')
        self.alignment = kwargs.get('alignment', '')
        self.experience = kwargs.get('experience', 0)
        
        # Stats and skills
        self.attributes = kwargs.get('attributes', {})
        self.skills = kwargs.get('skills', {})
        
        # Additional info
        self.inventory = kwargs.get('inventory', {})
        self.spells = kwargs.get('spells', {})
        self.features = kwargs.get('features', {})
        self.notes = kwargs.get('notes', '')
        
        # Parse JSON fields if they're strings
        for field in ['attributes', 'skills', 'inventory', 'spells', 'features']:
            value = getattr(self, field)
            if isinstance(value, str):
                try:
                    setattr(self, field, json.loads(value))
                except json.JSONDecodeError:
                    setattr(self, field, {})
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert character to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'player_id': self.player_id,
            'guild_id': self.guild_id,
            'character_class': self.character_class,
            'level': self.level,
            'race': self.race,
            'background': self.background,
            'alignment': self.alignment,
            'experience': self.experience,
            'attributes': json.dumps(self.attributes),
            'skills': json.dumps(self.skills),
            'inventory': json.dumps(self.inventory),
            'spells': json.dumps(self.spells),
            'features': json.dumps(self.features),
            'notes': self.notes
        }
    
    def get_ability_modifier(self, ability: str) -> int:
        """Get ability modifier for a stat"""
        ability = ability.lower()
        if ability in self.attributes:
            score = self.attributes[ability]
            return (score - 10) // 2
        return 0
    
    def get_skill_bonus(self, skill: str) -> int:
        """Get total bonus for a skill"""
        skill = skill.lower()
        if skill not in self.skills:
            return 0
        
        skill_info = self.skills[skill]
        ability = skill_info.get('ability', 'dexterity')
        proficient = skill_info.get('proficient', False)
        expertise = skill_info.get('expertise', False)
        
        modifier = self.get_ability_modifier(ability)
        prof_bonus = self.get_proficiency_bonus()
        
        if expertise:
            return modifier + (prof_bonus * 2)
        elif proficient:
            return modifier + prof_bonus
        else:
            return modifier
    
    def get_proficiency_bonus(self) -> int:
        """Get character's proficiency bonus based on level"""
        return 1 + ((self.level - 1) // 4)
    
    def to_embed(self) -> discord.Embed:
        """Create a Discord embed for this character"""
        embed = discord.Embed(
            title=self.name,
            description=f"{self.race} {self.character_class} (Level {self.level})",
            color=discord.Color.blue()
        )
        
        # Basic info
        embed.add_field(
            name="Basic Info",
            value=f"**Background:** {self.background}\n"
                  f"**Alignment:** {self.alignment}\n"
                  f"**XP:** {self.experience}",
            inline=False
        )
        
        # Attributes
        attr_text = ""
        for attr, value in self.attributes.items():
            modifier = self.get_ability_modifier(attr)
            sign = "+" if modifier >= 0 else ""
            attr_text += f"**{attr.upper()}:** {value} ({sign}{modifier})\n"
        
        embed.add_field(name="Attributes", value=attr_text or "None", inline=True)
        
        # Skills
        if self.skills:
            skill_text = ""
            for skill, info in self.skills.items():
                if info.get('proficient', False):
                    bonus = self.get_skill_bonus(skill)
                    sign = "+" if bonus >= 0 else ""
                    skill_text += f"**{skill.title()}:** {sign}{bonus}\n"
            
            if skill_text:
                embed.add_field(name="Proficient Skills", value=skill_text, inline=True)
        
        return embed


class CharacterManager:
    """Manages character creation, storage, and retrieval"""
    
    def __init__(self, bot):
        """Initialize the character manager"""
        self.bot = bot
        self.db = DatabaseManager()
        self.characters_cache = {}  # player_id -> {character_id -> Character}
        
        # Ensure character templates directory exists
        os.makedirs("config/templates", exist_ok=True)
        
        # Create default character template if it doesn't exist
        self._create_default_template()
        
        logger.info("Character manager initialized")
    
    def _create_default_template(self):
        """Create default character template"""
        template_path = "config/templates/dnd5e_character.json"
        
        if not os.path.exists(template_path):
            default_template = {
                "attributes": {
                    "strength": 10,
                    "dexterity": 10,
                    "constitution": 10,
                    "intelligence": 10,
                    "wisdom": 10,
                    "charisma": 10
                },
                "skills": {
                    "acrobatics": {"ability": "dexterity", "proficient": False},
                    "animal handling": {"ability": "wisdom", "proficient": False},
                    "arcana": {"ability": "intelligence", "proficient": False},
                    "athletics": {"ability": "strength", "proficient": False},
                    "deception": {"ability": "charisma", "proficient": False},
                    "history": {"ability": "intelligence", "proficient": False},
                    "insight": {"ability": "wisdom", "proficient": False},
                    "intimidation": {"ability": "charisma", "proficient": False},
                    "investigation": {"ability": "intelligence", "proficient": False},
                    "medicine": {"ability": "wisdom", "proficient": False},
                    "nature": {"ability": "intelligence", "proficient": False},
                    "perception": {"ability": "wisdom", "proficient": False},
                    "performance": {"ability": "charisma", "proficient": False},
                    "persuasion": {"ability": "charisma", "proficient": False},
                    "religion": {"ability": "intelligence", "proficient": False},
                    "sleight of hand": {"ability": "dexterity", "proficient": False},
                    "stealth": {"ability": "dexterity", "proficient": False},
                    "survival": {"ability": "wisdom", "proficient": False}
                }
            }
            
            os.makedirs(os.path.dirname(template_path), exist_ok=True)
            with open(template_path, "w") as f:
                json.dump(default_template, f, indent=4)
            
            logger.info(f"Created default character template at {template_path}")
    
    def create_character(self, player_id: str, guild_id: str, name: str, **kwargs) -> Character:
        """Create a new character"""
        # Create character object
        character_data = {
            'player_id': player_id,
            'guild_id': guild_id,
            'name': name,
            **kwargs
        }
        
        # Apply default template for missing fields
        template_path = "config/templates/dnd5e_character.json"
        if os.path.exists(template_path):
            try:
                with open(template_path, "r") as f:
                    template = json.load(f)
                
                # Apply template defaults for attributes and skills
                if 'attributes' not in character_data and 'attributes' in template:
                    character_data['attributes'] = template['attributes']
                if 'skills' not in character_data and 'skills' in template:
                    character_data['skills'] = template['skills']
            except Exception as e:
                logger.error(f"Error loading character template: {e}")
        
        character = Character(**character_data)
        
        # Save to database
        try:
            character_id = self.db.insert('characters', character.to_dict())
            character.id = character_id
            
            # Update cache
            if player_id not in self.characters_cache:
                self.characters_cache[player_id] = {}
            self.characters_cache[player_id][character_id] = character
            
            logger.info(f"Created character '{name}' for player {player_id}")
            return character
        except Exception as e:
            logger.error(f"Error creating character: {e}")
            return None
    
    def get_character(self, character_id: int) -> Optional[Character]:
        """Get a character by ID"""
        # Check cache first
        for player_characters in self.characters_cache.values():
            if character_id in player_characters:
                return player_characters[character_id]
        
        # Query database
        try:
            character_data = self.db.fetchone("SELECT * FROM characters WHERE id = ?", (character_id,))
            if not character_data:
                return None
            
            character = Character(**character_data)
            
            # Update cache
            player_id = character.player_id
            if player_id not in self.characters_cache:
                self.characters_cache[player_id] = {}
            self.characters_cache[player_id][character_id] = character
            
            return character
        except Exception as e:
            logger.error(f"Error getting character {character_id}: {e}")
            return None
    
    def get_player_characters(self, player_id: str, guild_id: str = None) -> List[Character]:
        """Get all characters for a player, optionally filtered by guild"""
        try:
            if guild_id:
                query = "SELECT * FROM characters WHERE player_id = ? AND guild_id = ?"
                params = (player_id, guild_id)
            else:
                query = "SELECT * FROM characters WHERE player_id = ?"
                params = (player_id,)
            
            character_data_list = self.db.fetchall(query, params)
            characters = [Character(**data) for data in character_data_list]
            
            # Update cache
            if player_id not in self.characters_cache:
                self.characters_cache[player_id] = {}
            
            for character in characters:
                self.characters_cache[player_id][character.id] = character
            
            return characters
        except Exception as e:
            logger.error(f"Error getting characters for player {player_id}: {e}")
            return []
    
    def update_character(self, character: Character) -> bool:
        """Update a character"""
        if not character.id:
            logger.error("Cannot update character without ID")
            return False
        
        try:
            character_dict = character.to_dict()
            # Remove ID from update data
            character_id = character_dict.pop('id')
            
            # Add updated timestamp
            character_dict['updated_at'] = 'CURRENT_TIMESTAMP'
            
            # Update database
            self.db.update('characters', character_dict, 'id = ?', (character_id,))
            
            # Update cache
            if character.player_id in self.characters_cache:
                self.characters_cache[character.player_id][character_id] = character
            
            logger.info(f"Updated character {character_id} ({character.name})")
            return True
        except Exception as e:
            logger.error(f"Error updating character {character.id}: {e}")
            return False
    
    def delete_character(self, character_id: int) -> bool:
        """Delete a character"""
        try:
            # Get character first to know the player_id
            character = self.get_character(character_id)
            if not character:
                logger.warning(f"Character {character_id} not found for deletion")
                return False
            
            # Delete from database
            self.db.delete('characters', 'id = ?', (character_id,))
            
            # Remove from cache
            if character.player_id in self.characters_cache and character_id in self.characters_cache[character.player_id]:
                del self.characters_cache[character.player_id][character_id]
            
            logger.info(f"Deleted character {character_id} ({character.name})")
            return True
        except Exception as e:
            logger.error(f"Error deleting character {character_id}: {e}")
            return False
    
    def export_character(self, character_id: int, format: str = 'json') -> Optional[str]:
        """Export a character to the specified format"""
        character = self.get_character(character_id)
        if not character:
            return None
        
        try:
            # Create exports directory
            os.makedirs("data/exports", exist_ok=True)
            
            if format.lower() == 'json':
                # Export as JSON
                filename = f"data/exports/character_{character.name}_{character_id}.json"
                with open(filename, 'w') as f:
                    json.dump(character.to_dict(), f, indent=4)
                return filename
            else:
                logger.error(f"Unsupported export format: {format}")
                return None
        except Exception as e:
            logger.error(f"Error exporting character {character_id}: {e}")
            return None
    
    def import_character(self, player_id: str, guild_id: str, file_path: str) -> Optional[Character]:
        """Import a character from a file"""
        try:
            with open(file_path, 'r') as f:
                character_data = json.load(f)
            
            # Override player_id and guild_id with current values
            character_data['player_id'] = player_id
            character_data['guild_id'] = guild_id
            
            # Remove ID if present (to create a new character)
            character_data.pop('id', None)
            
            # Create character
            return self.create_character(player_id, guild_id, character_data.get('name', 'Imported Character'), **character_data)
        except Exception as e:
            logger.error(f"Error importing character from {file_path}: {e}")
            return None