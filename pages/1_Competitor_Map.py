import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.title("🗺️ Pho Competitors in Greater Harrisburg Area")

st.markdown("""
### Competitive Intelligence Dashboard
This map shows all pho restaurants in the Greater Harrisburg area with:
- **Bayesian Average Rating** (confidence-weighted using m=50)
- **Price Index** (average of Pho Dac Biet L and Pho 2 Topping L)
- **Geographic distribution** of competitors
""")

try:
    # Load competitors data
    competitors = pd.read_csv('Pho Competitors.csv')
    
    # --- BAYESIAN AVERAGE RATING ---
    # Formula: WR = (v*R + m*C) / (v + m)
    # v = number of reviews for this restaurant
    # R = average rating for this restaurant
    # m = minimum reviews required (confidence threshold) = 50
    # C = mean rating across all restaurants
    
    m = 50  # Confidence threshold
    C = competitors['Google Rating'].mean()  # Mean rating across all shops
    
    competitors['Bayesian_Rating'] = (
        (competitors['Google Reviews'] * competitors['Google Rating'] + m * C) / 
        (competitors['Google Reviews'] + m)
    )
    
    # --- PRICE INDEX ---
    # Average of Pho Dac Biet L and Pho 2 Topping equivalent L
    competitors['Price_Index'] = (
        competitors['Pho Dac Biet L'] + competitors['Pho 2 Topping equivalent L']
    ) / 2
    
    # --- GEOCODING ---
    # Manually add lat/long for Central PA addresses
    location_coords = {
        "4401 Carlisle Pike Ste F, Camp Hill, PA 17011": (40.2401, -76.9358),
        "2800 Paxton St, Harrisburg, PA 17111": (40.2737, -76.8294),
        "4830 Carlisle Pike. Ste D8. Mechanicsburg, PA": (40.2139, -77.0486),
        "5490 Derry St B, Harrisburg, PA 17111": (40.2856, -76.7953),
        "6003 Allentown Blvd, Harrisburg, PA 17112": (40.3141, -76.7836),
        "1030 S 13th St, Harrisburg, PA 17104": (40.2556, -76.8756),
        "314 S 10th St, Lemoyne, PA 17043": (40.2365, -76.8944),
        "304 S Progress Ave rear, Harrisburg, PA 17109": (40.2661, -76.8458),
        "304 Reily St, Harrisburg, PA 17102": (40.2638, -76.8867)
    }
    
    competitors['Latitude'] = competitors['Address'].map(lambda x: location_coords.get(x, (None, None))[0])
    competitors['Longitude'] = competitors['Address'].map(lambda x: location_coords.get(x, (None, None))[1])
    
    # --- TOOLTIP TEXT ---
    # Show address and Pho 2 Topping price on hover
    competitors['Hover_Text'] = (
        '<b>' + competitors['Restaurants'] + '</b><br><br>' +
        '<b>Address:</b> ' + competitors['Address'] + '<br>' +
        '<b>Pho 2 Topping Price:</b> $' + competitors['Pho 2 Topping equivalent L'].round(2).astype(str) + '<br><br>' +
        '<b>Bayesian Rating:</b> ' + competitors['Bayesian_Rating'].round(2).astype(str) + '<br>' +
        '<b>Google Rating:</b> ' + competitors['Google Rating'].astype(str) + ' (' + competitors['Google Reviews'].astype(str) + ' reviews)<br>' +
        '<b>Price Index:</b> $' + competitors['Price_Index'].round(2).astype(str)
    )
    
    # --- SUMMARY STATISTICS ---
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Competitors", len(competitors))
    with col2:
        st.metric("Avg Price Index", f"${competitors['Price_Index'].mean():.2f}")
    with col3:
        st.metric("Avg Bayesian Rating", f"{competitors['Bayesian_Rating'].mean():.2f}")
    with col4:
        bamboo = competitors[competitors['Restaurants'] == 'Bamboo Pho and Tea'].iloc[0]
        st.metric("Bamboo's Rank (Price)", 
                 f"{(competitors['Price_Index'] < bamboo['Price_Index']).sum() + 1} of {len(competitors)}")
    
    st.divider()
    
    # --- INTERACTIVE MAP ---
    fig_map = go.Figure()
    
    # Add all competitors
    fig_map.add_trace(go.Scattermapbox(
        lat=competitors['Latitude'],
        lon=competitors['Longitude'],
        mode='markers',
        marker=dict(
            size=competitors['Bayesian_Rating'] * 12,  # Size based on Bayesian rating
            color=competitors['Price_Index'],
            colorscale='RdYlGn_r',  # Red (expensive) to Green (cheap)
            showscale=True,
            colorbar=dict(
                title="Price Index ($)",
                x=1.02
            ),
            sizemode='diameter'
        ),
        text=competitors['Hover_Text'],
        hovertemplate='%{text}<extra></extra>',
        name='Competitors'
    ))
    
    # Highlight Bamboo Pho with a gold star
    bamboo = competitors[competitors['Restaurants'] == 'Bamboo Pho and Tea'].iloc[0]
    fig_map.add_trace(go.Scattermapbox(
        lat=[bamboo['Latitude']],
        lon=[bamboo['Longitude']],
        mode='markers',
        marker=dict(
            size=30,
            color='gold',
            symbol='star'
        ),
        text=bamboo['Hover_Text'],
        hovertemplate='%{text}<extra></extra>',
        name='⭐ Bamboo Pho and Tea',
        showlegend=True
    ))
    
    fig_map.update_layout(
        mapbox=dict(
            style="open-street-map",
            center=dict(lat=40.26, lon=-76.88),
            zoom=10.5
        ),
        height=700,
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor="rgba(255,255,255,0.8)"
        )
    )
    
    st.plotly_chart(fig_map, use_container_width=True)
    
    # --- LEGEND ---
    st.markdown("### Map Legend")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**🔵 Bubble Size**")
        st.caption("Based on Bayesian Average Rating")
        st.caption(f"Range: {competitors['Bayesian_Rating'].min():.2f} - {competitors['Bayesian_Rating'].max():.2f}")
    
    with col2:
        st.markdown("**🎨 Bubble Color**")
        st.caption("Based on Price Index")
        st.caption("🟢 Green = Budget | 🟡 Yellow = Mid-range | 🔴 Red = Expensive")
    
    with col3:
        st.markdown("**⭐ Gold Star**")
        st.caption("Bamboo Pho and Tea")
        st.caption(f"Bayesian Rating: {bamboo['Bayesian_Rating']:.2f}")
    
    st.divider()
    
    # --- BAYESIAN FORMULA EXPLANATION ---
    with st.expander("📊 About Bayesian Average Rating"):
        st.markdown(f"""
        ### Why Use Bayesian Average?
        
        Simple averages can be misleading when restaurants have very different numbers of reviews:
        - A restaurant with 5 reviews and 5.0 rating shouldn't rank higher than one with 500 reviews and 4.7 rating
        - Bayesian average adds confidence weighting based on review volume
        
        ### Formula
        
        **WR = (v × R + m × C) / (v + m)**
        
        Where:
        - **WR** = Weighted Rating (Bayesian Average)
        - **v** = Number of reviews for this restaurant
        - **R** = Average rating for this restaurant
        - **m** = Confidence threshold (set to **50**)
        - **C** = Mean rating across all restaurants (**{C:.2f}**)
        
        ### Effect
        
        - Restaurants with **many reviews** → Rating stays close to their actual average
        - Restaurants with **few reviews** → Rating pulled toward the overall mean
        - **m = 50** means a restaurant needs ~50 reviews to be fully trusted
        
        ### Example Calculations
        
        **Restaurant A:** 5.0 rating, 10 reviews  
        → Bayesian: **{(10 * 5.0 + 50 * C) / (10 + 50):.2f}**
        
        **Restaurant B:** 4.7 rating, 500 reviews  
        → Bayesian: **{(500 * 4.7 + 50 * C) / (500 + 50):.2f}**
        
        **Result:** Restaurant B ranks higher (more reliable data)
        """)
    
    st.divider()
    
    # --- COMPETITOR TABLE ---
    st.subheader("📋 Detailed Competitor Analysis")
    
    # Sort by Bayesian rating
    competitors_display = competitors[[
        'Restaurants', 'Google Rating', 'Google Reviews', 'Bayesian_Rating', 
        'Pho 2 Topping equivalent L', 'Price_Index', 'Address'
    ]].copy()
    
    competitors_display = competitors_display.sort_values('Bayesian_Rating', ascending=False)
    competitors_display['Rank'] = range(1, len(competitors_display) + 1)
    
    # Reorder columns
    competitors_display = competitors_display[[
        'Rank', 'Restaurants', 'Bayesian_Rating', 'Google Rating', 'Google Reviews',
        'Pho 2 Topping equivalent L', 'Price_Index', 'Address'
    ]]
    
    competitors_display.columns = [
        'Rank', 'Restaurant', 'Bayesian Rating', 'Google Rating', '# Reviews',
        'Pho 2 Topping ($)', 'Price Index ($)', 'Address'
    ]
    
    # Highlight Bamboo
    def highlight_bamboo(row):
        if 'Bamboo' in row['Restaurant']:
            return ['background-color: #FFD70020'] * len(row)
        return [''] * len(row)
    
    st.dataframe(
        competitors_display.style.apply(highlight_bamboo, axis=1).format({
            'Bayesian Rating': '{:.2f}',
            'Google Rating': '{:.1f}',
            'Pho 2 Topping ($)': '${:.2f}',
            'Price Index ($)': '${:.2f}'
        }),
        use_container_width=True,
        hide_index=True
    )
    
    # Bamboo's position
    bamboo_rank = (competitors_display['Restaurant'] == 'Bamboo Pho and Tea').idxmax() + 1
    st.info(f"⭐ **Bamboo Pho and Tea ranks #{bamboo_rank} of {len(competitors)} by Bayesian Rating**")
    
except Exception as e:
    st.error(f"Error loading competitor data: {e}")
