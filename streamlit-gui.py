import streamlit as st
import pandas as pd
from reach_frequency_calculator import ReachFrequencyCalculator

def create_gui():
    st.title("Reach & Frequency Calculator")
    
    # Create input sections
    st.header("Basic Inputs")
    col1, col2 = st.columns(2)
    
    with col1:
        total_universe = st.number_input(
            "Total Universe", 
            value=1,  # Changed initial value to 1
            min_value=1
        )
        
        total_impressions = st.number_input(
            "Total Impressions",
            value=1,  # Changed initial value to 1
            min_value=1
        )
    
    with col2:
        max_reach_percent = st.number_input(
            "Maximum Reach %",
            value=0.0,
            min_value=0.0,
            max_value=100.0
        )
        global_overlap_factor = st.number_input(
            "Global Overlap Factor",
            value=0.0,
            min_value=0.0,
            max_value=1.0
        )
    
    # Channel impressions input
    st.header("Channel Impressions")
    
    # Create a DataFrame for channel impressions with default 0 values
    default_channels = {
        "OOH": 0,
        "CTV": 0,
        "Creators": 0,
        "Music Streaming": 0,
        "Programmatic": 0,
        "Display": 0,
        "Social": 0,
        "Search": 0
    }
    
    # Convert to DataFrame for editing
    df = pd.DataFrame(
        [[channel, impressions] for channel, impressions in default_channels.items()],
        columns=['Channel', 'Impressions']
    )
    
    # Create an editable dataframe with locked channel names
    edited_df = st.data_editor(
        df,
        num_rows="fixed",
        disabled=["Channel"],
        column_config={
            "Channel": st.column_config.TextColumn(
                "Channel",
                help="Media channel name",
                width="medium",
            ),
            "Impressions": st.column_config.NumberColumn(
                "Impressions",
                help="Number of impressions",
                min_value=0,
                width="medium",
            )
        }
    )
    
    # Convert back to dictionary with integer values
    distributed_impressions = {
        channel: int(impressions) 
        for channel, impressions in zip(edited_df['Channel'], edited_df['Impressions'])
    }
    
    # Add a calculate button
    if st.button("Calculate Results"):
        calculator = ReachFrequencyCalculator(
            total_universe=total_universe,
            total_impressions=total_impressions,
            max_reach_percent=max_reach_percent,
            global_overlap_factor=global_overlap_factor,
            distributed_impressions=distributed_impressions,
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
        
        results = calculator.run_all_calculations()
        
        # Display results
        st.header("Results")
        
        # Channel contributions
        st.subheader("Channel Contributions")
        contrib_df = pd.DataFrame([
            {"Channel": channel, "Contribution": f"{contrib:.1f}%"}
            for channel, contrib in results['channel_contributions'].items()
        ])
        st.dataframe(contrib_df, hide_index=True)
        
        # Main metrics
        st.subheader("Reach Metrics")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Final Reach %", f"{results['final_reach_percent']:.1f}%")
        with col2:
            st.metric("Final Reach (Individuals)", f"{results['final_reach']:.0f}")
        with col3:
            st.metric("Average Frequency", f"{results['average_frequency']:.1f}")
        
        # Effective reach
        st.subheader("Effective Reach")
        effective_df = pd.DataFrame([
            {"Frequency": freq, "Reach": f"{reach:.1f}%"}
            for freq, reach in results['effective_reach'].items()
        ])
        st.dataframe(effective_df, hide_index=True)

if __name__ == "__main__":
    create_gui()
