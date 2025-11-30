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
        print(f"[BATTLE] Seed set to: {seed}")
        
    def set_pokemon(self, my_pokemon_name, opponent_pokemon_name):
        """Set the Pokémon for both players"""
        print(f"[BATTLE] Setting Pokémon - Mine: {my_pokemon_name}, Opponent: {opponent_pokemon_name}")
        
        # Set my Pokémon
        if my_pokemon_name and my_pokemon_name.lower() in self.pokemon_data:
            self.my_pokemon = self.pokemon_data[my_pokemon_name.lower()]
            print(f"[BATTLE] My Pokémon: {self.my_pokemon.name} (HP: {self.my_pokemon.current_hp})")
        else:
            print(f"[BATTLE] ERROR: My Pokémon '{my_pokemon_name}' not found!")
            
        # Set opponent's Pokémon  
        if opponent_pokemon_name and opponent_pokemon_name.lower() in self.pokemon_data:
            self.opponent_pokemon = self.pokemon_data[opponent_pokemon_name.lower()]
            print(f"[BATTLE] Opponent Pokémon: {self.opponent_pokemon.name} (HP: {self.opponent_pokemon.current_hp})")
        else:
            print(f"[BATTLE] ERROR: Opponent Pokémon '{opponent_pokemon_name}' not found!")
        
    def calculate_damage(self, attacker, defender, move_name):
        """Calculate damage using the deterministic formula"""
        if not attacker or not defender:
            print("[DAMAGE] ERROR: Attacker or defender is None!")
            return 0
            
        if move_name.lower() not in MOVES:
            print(f"[DAMAGE] ERROR: Move '{move_name}' not found!")
            return 0
            
        move = MOVES[move_name.lower()]
        level = 50  # Standard battle level
        
        print(f"[DAMAGE] {attacker.name} using {move_name} against {defender.name}")
        print(f"[DAMAGE] Move: {move}, Attacker HP: {attacker.current_hp}, Defender HP: {defender.current_hp}")
        
        # Determine attack and defense stats based on move category
        if move['category'] == 'physical':
            attack_stat = attacker.attack
            defense_stat = defender.defense
            print(f"[DAMAGE] Physical: ATK={attack_stat}, DEF={defense_stat}")
        else:  # special
            attack_stat = attacker.special_attack
            defense_stat = defender.special_defense
            print(f"[DAMAGE] Special: SP_ATK={attack_stat}, SP_DEF={defense_stat}")
            
        # Type effectiveness
        type_effectiveness = get_type_effectiveness(move['type'], defender.types)
        print(f"[DAMAGE] Type effectiveness: {type_effectiveness}x")
        
        # Random factor (deterministic due to shared seed)
        random_factor = random.uniform(0.85, 1.0)
        print(f"[DAMAGE] Random factor: {random_factor:.3f}")
        
        # Damage calculation formula
        damage = ((((2 * level / 5 + 2) * move['power'] * attack_stat / defense_stat) / 50) + 2) * type_effectiveness * random_factor
        
        final_damage = int(max(1, damage))  # Minimum 1 damage
        print(f"[DAMAGE] Calculated damage: {final_damage}")
        
        return final_damage
    
    def handle_attack_announce(self, move_name, is_opponent_attack=False):
        """Process an attack announcement"""
        print(f"[BATTLE] Handling attack: {move_name}, is_opponent: {is_opponent_attack}")
        
        if is_opponent_attack:
            # Opponent is attacking us
            attacker = self.opponent_pokemon
            defender = self.my_pokemon
            print(f"[BATTLE] Opponent {attacker.name} attacking my {defender.name}")
        else:
            # We are attacking opponent
            attacker = self.my_pokemon
            defender = self.opponent_pokemon
            print(f"[BATTLE] My {attacker.name} attacking opponent {defender.name}")
            
        if not attacker or not defender:
            print("[BATTLE] ERROR: Missing Pokémon for battle!")
            return {
                'attacker': "Unknown",
                'move_used': move_name,
                'remaining_health': 0,
                'damage_dealt': 0,
                'defender_hp_remaining': 0,
                'status_message': "ERROR: Pokémon not set up properly",
                'defender_fainted': False
            }
            
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
        
        print(f"[BATTLE] Attack result: {damage} damage, {defender.name} HP: {defender.current_hp}, Fainted: {defender_fainted}")
        
        return {
            'attacker': attacker.name,
            'move_used': move_name,
            'remaining_health': attacker.current_hp,
            'damage_dealt': damage,
            'defender_hp_remaining': defender.current_hp,
            'status_message': status_message,
            'defender_fainted': defender_fainted
        }
