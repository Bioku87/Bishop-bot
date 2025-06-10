"""
Bishop Bot - Dice Rolling System
Last updated: 2025-05-31 18:33:27 UTC by Bioku87
"""
import re
import random
import logging
from typing import Dict, List, Any, Optional, Tuple, Union

logger = logging.getLogger('bishop_bot.dice')

class DiceRoll:
    """Represents the result of a dice roll"""
    
    def __init__(self, expression: str, rolls: List[int], total: int, breakdown: str):
        self.expression = expression  # Original dice expression
        self.rolls = rolls  # Individual die results
        self.total = total  # Total result
        self.breakdown = breakdown  # Detailed breakdown with calculations
    
    def __str__(self) -> str:
        return f"{self.expression} = {self.total} [{', '.join(map(str, self.rolls))}]"


class DiceManager:
    """Handles dice rolling mechanics"""
    
    # Regex to match dice expressions like 2d6+3, 1d20-2, etc.
    DICE_PATTERN = re.compile(r'(\d+)d(\d+)(?:([+-])(\d+))?')
    
    # Advanced dice pattern with advantage/disadvantage and exploding dice
    ADV_DICE_PATTERN = re.compile(r'(?:(\d+))?d(\d+)((?:[+-]\d+|[adkxr!><]\d*)*)')
    
    # Regex to match operators in complex dice expressions
    OPERATORS = re.compile(r'([adkxr!><])(\d*)')
    
    def __init__(self):
        """Initialize the dice manager"""
        logger.info("Dice manager initialized")
    
    def roll_simple(self, num_dice: int, sides: int) -> List[int]:
        """Roll a number of dice with the given sides"""
        return [random.randint(1, sides) for _ in range(num_dice)]
    
    def parse_expression(self, expression: str) -> Tuple[int, int, str, int]:
        """Parse a dice expression into components"""
        match = self.DICE_PATTERN.match(expression.lower().replace(' ', ''))
        if not match:
            raise ValueError(f"Invalid dice expression: {expression}")
        
        num_dice = int(match.group(1))
        sides = int(match.group(2))
        
        # Get operator and modifier if present
        if match.group(3) and match.group(4):
            operator = match.group(3)
            modifier = int(match.group(4))
        else:
            operator = '+'
            modifier = 0
        
        return num_dice, sides, operator, modifier
    
    def roll(self, expression: str) -> DiceRoll:
        """Roll dice based on the given expression"""
        try:
            num_dice, sides, operator, modifier = self.parse_expression(expression)
            
            # Validate input
            if num_dice <= 0 or sides <= 0:
                raise ValueError(f"Invalid dice parameters: {num_dice}d{sides}")
            if num_dice > 100:
                raise ValueError(f"Too many dice: {num_dice} (max 100)")
            if sides > 1000:
                raise ValueError(f"Too many sides: {sides} (max 1000)")
            
            # Roll the dice
            rolls = self.roll_simple(num_dice, sides)
            dice_sum = sum(rolls)
            
            # Apply modifier
            if operator == '+':
                total = dice_sum + modifier
                breakdown = f"{dice_sum} + {modifier}" if modifier != 0 else str(dice_sum)
            else:  # operator == '-'
                total = dice_sum - modifier
                breakdown = f"{dice_sum} - {modifier}" if modifier != 0 else str(dice_sum)
            
            return DiceRoll(expression, rolls, total, breakdown)
        except Exception as e:
            logger.error(f"Error rolling dice: {e}")
            raise
    
    def roll_advanced(self, expression: str) -> DiceRoll:
        """Roll dice with advanced options"""
        try:
            match = self.ADV_DICE_PATTERN.match(expression.lower().replace(' ', ''))
            if not match:
                raise ValueError(f"Invalid dice expression: {expression}")
            
            num_dice = int(match.group(1)) if match.group(1) else 1
            sides = int(match.group(2))
            options = match.group(3) if match.group(3) else ""
            
            # Validate input
            if num_dice <= 0 or sides <= 0:
                raise ValueError(f"Invalid dice parameters: {num_dice}d{sides}")
            if num_dice > 100:
                raise ValueError(f"Too many dice: {num_dice} (max 100)")
            if sides > 1000:
                raise ValueError(f"Too many sides: {sides} (max 1000)")
            
            # Parse options
            advantage = False
            disadvantage = False
            keep_highest = 0
            keep_lowest = 0
            exploding = False
            reroll_threshold = 0
            modifier = 0
            
            # Extract modifier
            mod_match = re.search(r'([+-])(\d+)$', options)
            if mod_match:
                mod_operator = mod_match.group(1)
                mod_value = int(mod_match.group(2))
                modifier = mod_value if mod_operator == '+' else -mod_value
                options = options[:mod_match.start()]
            
            # Parse special operators
            for op_match in self.OPERATORS.finditer(options):
                op = op_match.group(1)
                value = int(op_match.group(2)) if op_match.group(2) else 0
                
                if op == 'a':
                    advantage = True
                elif op == 'd':
                    disadvantage = True
                elif op == 'k':
                    keep_highest = value if value else num_dice
                elif op == 'x':
                    keep_lowest = value if value else num_dice
                elif op == '!':
                    exploding = True
                elif op == 'r':
                    reroll_threshold = value if value else 1
            
            # Roll dice with options
            rolls = []
            
            # Handle advantage/disadvantage
            if advantage or disadvantage:
                # Roll twice
                roll1 = self.roll_simple(num_dice, sides)
                roll2 = self.roll_simple(num_dice, sides)
                
                if advantage:
                    rolls = roll1 if sum(roll1) > sum(roll2) else roll2
                    breakdown = f"Advantage: {sum(roll1)} vs {sum(roll2)}"
                else:  # disadvantage
                    rolls = roll1 if sum(roll1) < sum(roll2) else roll2
                    breakdown = f"Disadvantage: {sum(roll1)} vs {sum(roll2)}"
            else:
                # Standard roll with options
                if exploding:
                    # Exploding dice (roll again if max value)
                    temp_rolls = []
                    for _ in range(num_dice):
                        roll = random.randint(1, sides)
                        temp_rolls.append(roll)
                        while roll == sides:
                            roll = random.randint(1, sides)
                            temp_rolls.append(roll)
                    rolls = temp_rolls
                    breakdown = f"Exploding: {rolls}"
                else:
                    # Normal rolls
                    rolls = self.roll_simple(num_dice, sides)
                    breakdown = f"Rolls: {rolls}"
                
                # Handle rerolls
                if reroll_threshold > 0:
                    for i, roll in enumerate(rolls):
                        if roll <= reroll_threshold:
                            rolls[i] = random.randint(1, sides)
                    breakdown += f" (Rerolls: {reroll_threshold}+)"
                
                # Handle keeping highest/lowest
                if keep_highest > 0 and keep_highest < len(rolls):
                    sorted_rolls = sorted(rolls, reverse=True)
                    kept_rolls = sorted_rolls[:keep_highest]
                    rolls = kept_rolls
                    breakdown += f" (Keep highest {keep_highest})"
                
                if keep_lowest > 0 and keep_lowest < len(rolls):
                    sorted_rolls = sorted(rolls)
                    kept_rolls = sorted_rolls[:keep_lowest]
                    rolls = kept_rolls
                    breakdown += f" (Keep lowest {keep_lowest})"
            
            # Calculate total
            total = sum(rolls) + modifier
            
            # Update breakdown with modifier
            if modifier != 0:
                modifier_sign = '+' if modifier > 0 else '-'
                modifier_abs = abs(modifier)
                breakdown += f" {modifier_sign} {modifier_abs}"
            
            return DiceRoll(expression, rolls, total, breakdown)
        except Exception as e:
            logger.error(f"Error rolling advanced dice: {e}")
            raise
    
    def roll_with_context(self, expression: str, character=None) -> DiceRoll:
        """Roll dice with character context for ability checks, etc."""
        try:
            # Check if this is an ability or skill check
            ability_match = re.match(r'(\w+)\s+check', expression.lower())
            skill_match = re.match(r'(\w+(?:\s+\w+)?)\s+skill', expression.lower())
            
            if character and ability_match:
                # Ability check
                ability = ability_match.group(1).lower()
                modifier = character.get_ability_modifier(ability)
                mod_sign = '+' if modifier >= 0 else ''
                
                # Roll 1d20 + ability modifier
                dice_expr = f"1d20{mod_sign}{modifier}"
                result = self.roll(dice_expr)
                result.expression = f"{ability.upper()} check ({dice_expr})"
                return result
            
            elif character and skill_match:
                # Skill check
                skill = skill_match.group(1).lower()
                skill_bonus = character.get_skill_bonus(skill)
                mod_sign = '+' if skill_bonus >= 0 else ''
                
                # Roll 1d20 + skill bonus
                dice_expr = f"1d20{mod_sign}{skill_bonus}"
                result = self.roll(dice_expr)
                result.expression = f"{skill.title()} check ({dice_expr})"
                return result
            
            else:
                # Standard roll
                if 'd' not in expression:
                    # Default to d20 if just a number or modifier is provided
                    if re.match(r'^[+-]?\d+$', expression):
                        mod = int(expression)
                        mod_sign = '+' if mod >= 0 else ''
                        expression = f"1d20{mod_sign}{mod}"
                    else:
                        expression = "1d20"
                
                # Try advanced roll first, fall back to simple roll
                try:
                    return self.roll_advanced(expression)
                except ValueError:
                    return self.roll(expression)
                
        except Exception as e:
            logger.error(f"Error in roll_with_context: {e}")
            # Fall back to simple roll
            try:
                return self.roll(expression)
            except:
                # Last resort, just roll 1d20
                return self.roll("1d20")
    
    def parse_dice_in_text(self, text: str) -> List[DiceRoll]:
        """Parse and roll any dice expressions found in text"""
        results = []
        
        # Find all dice expressions in the text
        expressions = []
        
        # Look for standard expressions like 2d6+3
        standard_matches = re.finditer(r'\b(\d+d\d+(?:[+-]\d+)?)\b', text)
        expressions.extend([m.group(1) for m in standard_matches])
        
        # Look for advanced expressions like d20a+5
        advanced_matches = re.finditer(r'\b(?:\d+)?d\d+(?:[adkxr!><]\d*)*(?:[+-]\d+)?\b', text)
        expressions.extend([m.group(0) for m in advanced_matches])
        
        # Remove duplicates and sort by length (longest first)
        expressions = list(set(expressions))
        expressions.sort(key=len, reverse=True)
        
        # Roll each expression
        for expr in expressions:
            try:
                result = self.roll_with_context(expr)
                results.append(result)
            except:
                # Skip invalid expressions
                pass
        
        return results