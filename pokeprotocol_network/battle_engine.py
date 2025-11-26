import random
from moves import MOVES, get_type_effectiveness

class BattleEngine:
    def __init__(self, pokemon_data):
        self.pokemon_data = pokemon_data
        self.seed = None
        self.my_pokemon = None
        self.opponent_pokemon = None
        self.my_stat_boosts = {'special_attack_uses': 5, 'special_defense_uses': 5}
        self.opponent_stat_boosts = {'special_attack_uses': 5, 'special_defense_uses': 5}
        self.is_my_turn = False
        self.current_move = None
        
    def set_seed(self, seed):
        """Set the random seed for deterministic calculations"""
        self.seed = seed
        random.seed(seed)
        
    def set_pokemon(self, my_pokemon_name, opponent_pokemon_name):
        """Set the Pokémon for both players"""
        self.my_pokemon = self.pokemon_data.get(my_pokemon_name.lower())
        self.opponent_pokemon = self.pokemon_data.get(opponent_pokemon_name.lower())
        
    def calculate_damage(self, attacker, defender, move_name, use_special_attack_boost=False, use_special_defense_boost=False):
        """Calculate damage using the deterministic formula"""
        if move_name.lower() not in MOVES:
            return 0
            
        move = MOVES[move_name.lower()]
        level = 50  # Standard battle level
        
        # Determine attack and defense stats based on move category
        if move['category'] == 'physical':
            attack_stat = attacker.attack
            defense_stat = defender.defense
        else:  # special
            attack_stat = attacker.special_attack
            defense_stat = defender.special_defense
            
        # Apply stat boosts if used
        if use_special_attack_boost:
            attack_stat = int(attack_stat * 1.5)  # 50% boost
        if use_special_defense_boost:
            defense_stat = int(defense_stat * 1.5)  # 50% boost
            
        # Type effectiveness
        type_effectiveness = get_type_effectiveness(move['type'], defender.types)
        
        # Random factor (deterministic due to shared seed)
        random_factor = random.uniform(0.85, 1.0)
        
        # Damage calculation formula
        damage = ((((2 * level / 5 + 2) * move['power'] * attack_stat / defense_stat) / 50) + 2) * type_effectiveness * random_factor
        
        return int(max(1, damage))  # Minimum 1 damage
    
    def handle_attack_announce(self, move_name, is_opponent_attack=False):
        """Process an attack announcement"""
        self.current_move = move_name
        
        if is_opponent_attack:
            # Opponent is attacking us
            attacker = self.opponent_pokemon
            defender = self.my_pokemon
        else:
            # We are attacking opponent
            attacker = self.my_pokemon
            defender = self.opponent_pokemon
            
        # Calculate damage
        damage = self.calculate_damage(attacker, defender, move_name)
        
        # Apply damage
        defender_fainted = defender.take_damage(damage)
        
        # Generate status message
        effectiveness = get_type_effectiveness(MOVES[move_name.lower()]['type'], defender.types)
        if effectiveness >= 2.0:
            effectiveness_text = "It was super effective!"
        elif effectiveness <= 0.5:
            effectiveness_text = "It's not very effective..."
        else:
            effectiveness_text = ""
            
        status_message = f"{attacker.name} used {move_name}! {effectiveness_text}".strip()
        
        return {
            'attacker': attacker.name,
            'move_used': move_name,
            'remaining_health': attacker.current_hp,
            'damage_dealt': damage,
            'defender_hp_remaining': defender.current_hp,
            'status_message': status_message,
            'defender_fainted': defender_fainted
        }
