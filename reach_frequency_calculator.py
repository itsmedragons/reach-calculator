import numpy as np
from typing import Dict, Optional, Tuple

class ReachFrequencyCalculator:
    def __init__(
        self,
        total_universe: int,
        total_impressions: int,
        max_reach_percent: float,
        global_overlap_factor: float,
        distributed_impressions: Dict[str, int],
        channel_penetration: Dict[str, float],
        efficiency_factors: Dict[str, float]
    ):
        # Input validation with custom thresholds
        if total_universe < 1000000:
            raise ValueError("Total universe must be at least 1,000,000")
        
        if total_impressions < 10000:
            raise ValueError("Total impressions must be at least 10,000")
            
        # Ensure max reach percent is between 0 and 99.8
        if not 0 <= max_reach_percent <= 99.8:
            raise ValueError("Maximum reach percentage must be between 0 and 99.8")
        
        # Ensure overlap factor is between 0.35 and 0.6
        if not 0.35 <= global_overlap_factor <= 0.6:
            raise ValueError("Global overlap factor must be between 0.35 and 0.6")
        
        self.total_universe = total_universe
        self.total_impressions = total_impressions
        self.max_reach_percent = max_reach_percent
        self.global_overlap_factor = global_overlap_factor
        self.distributed_impressions = distributed_impressions
        self.channel_penetration = channel_penetration
        self.efficiency_factors = efficiency_factors
        
        # Initialize calculated values
        self.channel_reach = {}
        self.channel_contributions = {}
        self.raw_total_reach = 0
        self.overlapped_reach = 0
        self.final_reach = 0
        self.average_frequency = 0
        self.effective_reach = {}

    def calculate_channel_reach(self) -> Tuple[Dict[str, float], Dict[str, float]]:
        """Calculate reach for each channel and their contribution percentages."""
        total_channel_reach = 0
        
        for channel, impressions in self.distributed_impressions.items():
            if channel in self.channel_penetration:
                penetration = self.channel_penetration[channel]
                max_possible_reach = penetration * self.total_universe
                
                # Modified reach calculation with safety bounds
                if impressions > 0:
                    # Use modified reach formula for more stable results with small numbers
                    reach = max_possible_reach * (1 - np.exp(-impressions / max_possible_reach))
                    reach = min(reach, max_possible_reach)  # Cap at maximum possible reach
                    self.channel_reach[channel] = max(0, reach)  # Ensure non-negative
                    total_channel_reach += self.channel_reach[channel]
                else:
                    self.channel_reach[channel] = 0
        
        # Calculate channel contributions
        if total_channel_reach > 0:
            for channel, reach in self.channel_reach.items():
                self.channel_contributions[channel] = (reach / total_channel_reach) * 100
        else:
            for channel in self.channel_reach.keys():
                self.channel_contributions[channel] = 0
                
        return self.channel_reach, self.channel_contributions

    def calculate_total_reach(self) -> float:
        """Calculate total reach with improved bounds checking."""
        if not self.channel_reach:
            self.raw_total_reach = 0
            self.final_reach = 0
            return 0
            
        self.raw_total_reach = sum(self.channel_reach.values())
        
        # Apply overlap adjustment with bounds
        overlap_reach = self.raw_total_reach * (1 - self.global_overlap_factor)
        
        # Calculate weighted efficiency
        total_weight = sum(self.channel_reach.values())
        if total_weight > 0:
            weighted_efficiency = sum(
                self.efficiency_factors.get(channel, 0.5) * reach 
                for channel, reach in self.channel_reach.items()
            ) / total_weight
        else:
            weighted_efficiency = 0.5  # Default efficiency if no reach
            
        # Apply efficiency and maximum reach cap
        reach_after_efficiency = overlap_reach * weighted_efficiency
        max_possible_reach = (self.max_reach_percent / 100) * self.total_universe
        
        # Ensure final reach is between 0 and max possible reach
        self.final_reach = min(max(0, reach_after_efficiency), max_possible_reach)
        
        return self.final_reach

    def calculate_frequency(self) -> float:
        """Calculate average frequency with improved bounds."""
        if self.final_reach <= 0:
            self.average_frequency = 0
            return 0
            
        raw_frequency = self.total_impressions / self.final_reach
        
        # Set reasonable bounds for frequency
        min_frequency = 1.0  # Minimum meaningful frequency
        max_frequency = 20.0  # Maximum reasonable frequency
        
        self.average_frequency = min(max(min_frequency, raw_frequency), max_frequency)
        return self.average_frequency

    def calculate_effective_reach(self, max_frequency: int = 6) -> Dict[str, float]:
        """Calculate effective reach with improved validation."""
        if self.final_reach <= 0 or self.average_frequency <= 0:
            return {f"{i}+": 0.0 for i in range(2, max_frequency + 1)}
            
        reach_percent = (self.final_reach / self.total_universe) * 100
        
        # Modified calculation to prevent extreme values
        x = 1 / max(1.0, self.average_frequency)
        
        self.effective_reach = {}
        current_reach = reach_percent
        
        for i in range(2, max_frequency + 1):
            previous_reach = current_reach
            current_reach = previous_reach * (1 - x)
            # Ensure reach values are between 0 and the maximum reach percent
            self.effective_reach[f"{i}+"] = min(max(0.0, current_reach), self.max_reach_percent)
            
        return self.effective_reach

    def run_all_calculations(self) -> Dict:
        """Run all calculations and return comprehensive results."""
        self.calculate_channel_reach()
        self.calculate_total_reach()
        self.calculate_frequency()
        self.calculate_effective_reach()
        
        return {
            'channel_contributions': self.channel_contributions,
            'raw_reach_percent': (self.raw_total_reach / self.total_universe) * 100,
            'overlapped_reach_percent': (self.overlapped_reach / self.total_universe) * 100,
            'final_reach': self.final_reach,
            'final_reach_percent': (self.final_reach / self.total_universe) * 100,
            'average_frequency': self.average_frequency,
            'effective_reach': self.effective_reach
        }
