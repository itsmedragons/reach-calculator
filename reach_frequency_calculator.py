import numpy as np
from typing import Dict, Optional, Tuple

class ReachFrequencyCalculator:
    """
    A calculator for media reach and frequency metrics that accounts for
    channel overlap, efficiency, and penetration rates.
    """
    
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
        self.total_universe = total_universe
        self.total_impressions = total_impressions
        self.max_reach_percent = max_reach_percent
        self.global_overlap_factor = global_overlap_factor
        self.distributed_impressions = distributed_impressions
        self.channel_penetration = channel_penetration
        self.efficiency_factors = efficiency_factors
        
        # Initialize calculated values
        self.channel_reach: Dict[str, float] = {}
        self.channel_contributions: Dict[str, float] = {}
        self.raw_total_reach: float = 0
        self.overlapped_reach: float = 0
        self.final_reach: float = 0
        self.average_frequency: float = 0
        self.effective_reach: Dict[str, float] = {}

    def calculate_channel_reach(self) -> Tuple[Dict[str, float], Dict[str, float]]:
        """
        Calculate reach for each channel and their contribution percentages.
        Channel contributions are calculated based on raw reach before efficiency factors.
        """
        # Calculate basic reach for each channel
        for channel, impressions in self.distributed_impressions.items():
            if channel in self.channel_penetration:
                penetration = self.channel_penetration[channel]
                max_possible_reach = penetration * self.total_universe
                # Basic reach calculation without efficiency factor
                self.channel_reach[channel] = max_possible_reach * (1 - np.exp(-impressions / self.total_universe))
        
        # Calculate raw total and contributions
        self.raw_total_reach = sum(self.channel_reach.values())
        
        # Calculate channel contributions based on raw reach
        for channel, reach in self.channel_reach.items():
            self.channel_contributions[channel] = (reach / self.raw_total_reach) * 100
            
        return self.channel_reach, self.channel_contributions

    def calculate_total_reach(self) -> float:
        """
        Calculate total reach by applying overlap adjustment first,
        then applying efficiency factors as a weighted average.
        """
        # Apply overlap adjustment
        self.overlapped_reach = self.raw_total_reach * (1 - self.global_overlap_factor)
        
        # Calculate weighted efficiency
        weighted_efficiency = sum(
            self.efficiency_factors[channel] * reach 
            for channel, reach in self.channel_reach.items()
        ) / self.raw_total_reach
        
        # Apply efficiency and maximum reach cap
        reach_after_efficiency = self.overlapped_reach * weighted_efficiency
        max_possible_reach = (self.max_reach_percent / 100) * self.total_universe
        self.final_reach = min(reach_after_efficiency, max_possible_reach)
        
        return self.final_reach

    def calculate_frequency(self) -> float:
        """
        Calculate average frequency based on total impressions and final reach.
        """
        if self.final_reach > 0:
            self.average_frequency = self.total_impressions / self.final_reach
        else:
            self.average_frequency = 0
        
        return self.average_frequency

    def calculate_effective_reach(self, max_frequency: int = 6) -> Dict[str, float]:
        """
        Calculate effective reach at different frequency levels (2+ through max_frequency+).
        Uses geometric distribution to estimate reach at each frequency level.
        """
        reach_percent = (self.final_reach / self.total_universe) * 100
        x = 1 / self.average_frequency
        
        current_reach = reach_percent
        for i in range(2, max_frequency + 1):
            previous_reach = current_reach
            current_reach = previous_reach * (1 - x)
            self.effective_reach[f"{i}+"] = current_reach
        
        return self.effective_reach

    def run_all_calculations(self) -> Dict[str, float]:
        """
        Run all calculations in the correct order and return comprehensive results.
        """
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

# Example usage with printing
if __name__ == "__main__":
    # Initialize calculator with your data
    calculator = ReachFrequencyCalculator(
        total_universe=68500000,
        total_impressions=611065006,
        max_reach_percent=98.8,
        global_overlap_factor=0.5,
        distributed_impressions={
            "OOH": 32905578,
            "CTV": 164905766,
            "Creators": 5000000,
            "Music Streaming": 20000000,
            "Programmatic": 10000000,
            "Display": 227900000,
            "Social": 251955000,
            "Search": 3922027
        },
        channel_penetration={
            "OOH": 0.08,
            "CTV": 0.75,
            "Creators": 0.17,
            "Music Streaming": 0.686,
            "Programmatic": 0.941,
            "Display": 0.941,
            "Social": 0.913,
            "Search": 0.65
        },
        efficiency_factors={
            "OOH": 0.5,
            "CTV": 0.8,
            "Creators": 0.8,
            "Music Streaming": 0.7,
            "Programmatic": 0.3,
            "Display": 0.6,
            "Social": 0.6,
            "Search": 0.7
        }
    )
    
    # Run calculations and get results
    results = calculator.run_all_calculations()
    
    # Print all results in a formatted way
    print("\nChannel Contributions:")
    for channel, contribution in results['channel_contributions'].items():
        print(f"{channel}: {contribution:.1f}%")
    
    print("\nReach Metrics:")
    print(f"Raw Total Reach: {results['raw_reach_percent']:.1f}%")
    print(f"Overlapped Reach: {results['overlapped_reach_percent']:.1f}%")
    print(f"Final Reach: {results['final_reach_percent']:.1f}%")
    print(f"Final Reach (Individuals): {results['final_reach']:,.0f}")
    print(f"Average Frequency: {results['average_frequency']:.1f}")
    
    print("\nEffective Reach:")
    for freq, reach in results['effective_reach'].items():
        print(f"{freq}: {reach:.1f}%")
