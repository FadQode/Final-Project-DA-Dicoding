import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import streamlit as st
from scipy.stats import ttest_ind
import folium
from streamlit_folium import st_folium



tiantan_df = pd.read_csv("AirData/Tiantan.csv")
dongsi_df = pd.read_csv("AirData/Dongsi.csv")

tiantan_df['date'] = pd.to_datetime(tiantan_df[['year', 'month', 'day', 'hour']])
dongsi_df['date'] = pd.to_datetime(dongsi_df[['year', 'month', 'day', 'hour']])

#Mengisi kekosongan variabel continu dengan method interpolate
#untuk variabel wd isi dengan unknown

tiantan_df[['TEMP', 'PRES', 'DEWP']] = tiantan_df[['TEMP', 'PRES', 'DEWP']].interpolate()
tiantan_df[['PM2.5', 'PM10', 'SO2', 'NO2', 'CO', 'O3', 'RAIN', 'WSPM']] = tiantan_df[['PM2.5', 'PM10', 'SO2', 'NO2', 'CO', 'O3', 'RAIN', 'WSPM']].interpolate()
tiantan_df.fillna(value="unknown", inplace=True)

#Mengisi kekosongan variabel continu dengan method interpolate
#untuk variabel wd isi dengan unknown

dongsi_df[['TEMP', 'PRES', 'DEWP']] = dongsi_df[['TEMP', 'PRES', 'DEWP']].interpolate()

dongsi_df[['PM2.5', 'PM10', 'SO2', 'NO2', 'CO', 'O3', 'RAIN', 'WSPM']] = dongsi_df[['PM2.5', 'PM10', 'SO2', 'NO2', 'CO', 'O3', 'RAIN', 'WSPM']].interpolate()

dongsi_df.fillna(value="unknown", inplace=True)



Q1 = tiantan_df['CO'].quantile(0.25)
Q3 = tiantan_df['CO'].quantile(0.75)
IQR = Q3 - Q1


lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR


outlier_mask = (tiantan_df['CO'] < lower_bound) | (tiantan_df['CO'] > upper_bound)


tiantan_df['CO'] = tiantan_df['CO'].mask(outlier_mask)  
tiantan_df['CO'] = tiantan_df['CO'].interpolate() 

columns_to_process = ['CO', 'O3']

for col in columns_to_process:
    Q1 = dongsi_df[col].quantile(0.25)
    Q3 = dongsi_df[col].quantile(0.75)
    IQR = Q3 - Q1

    # Step 2: Calculate the bounds for non-outliers
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR

    # Step 3: Create a mask for outliers
    outlier_mask = (dongsi_df[col] < lower_bound) | (dongsi_df[col] > upper_bound)

    # Step 4: Mask the outliers
    dongsi_df[col] = dongsi_df[col].mask(outlier_mask)

    # Step 5: Interpolate the masked values
    dongsi_df[col] = dongsi_df[col].interpolate()
combined = pd.merge(tiantan_df, dongsi_df, on=['year', 'month', 'day', 'hour'], suffixes=('_tiangtan', '_dongsi'))
combined['datetime'] = pd.to_datetime(combined[['year', 'month', 'day', 'hour']])
pollutants = ['PM2.5', 'PM10', 'SO2', 'NO2', 'CO', 'O3']

# Membuat pivot table berisi tingkat rerata polutan per bulannya di kedua distrik
# Menghitung rata-rata polusi per bulan untuk masing-masing distrik
monthly_avg_tiangtan = combined.groupby(['year', 'month'])[[f'{pollutant}_tiangtan' for pollutant in pollutants]].mean()
monthly_avg_dongsi = combined.groupby(['year', 'month'])[[f'{pollutant}_dongsi' for pollutant in pollutants]].mean()

# Menggabungkan rata-rata bulanan dari kedua distrik menggunakan merge
monthly_avg = pd.merge(monthly_avg_tiangtan.reset_index(), 
                       monthly_avg_dongsi.reset_index(), 
                       on=['year', 'month'], 
                       suffixes=('_tiangtan', '_dongsi'))
monthly_avg['Tahun_Bulan'] = monthly_avg['year'].astype(str) + "-" + monthly_avg['month'].astype(str)

# Mencari bulan dengan tingkat polusi tertinggi untuk masing-masing distrik
highest_pollution_tiangtan = monthly_avg[[f'{pollutant}_tiangtan' for pollutant in pollutants]].max()
highest_month_tiangtan = monthly_avg.loc[monthly_avg[[f'{pollutant}_tiangtan' for pollutant in pollutants]].idxmax().max()]

highest_pollution_dongsi = monthly_avg[[f'{pollutant}_dongsi' for pollutant in pollutants]].max()
highest_month_dongsi = monthly_avg.loc[monthly_avg[[f'{pollutant}_dongsi' for pollutant in pollutants]].idxmax().max()]

# Membuat pivot table untuk mendapatkan nilai maksimum per jam untuk setiap polutan di masing-masing distrik
pivot_tables_tiangtan = {}
pivot_tables_dongsi = {}

for pollutant in pollutants:
    # Pivot table untuk Tiangtan
    pivot_table_tiangtan = combined.pivot_table(values=pollutant + '_tiangtan', 
                                                index='hour', 
                                                aggfunc='mean')
    pivot_tables_tiangtan[pollutant] = pivot_table_tiangtan
    
    # Pivot table untuk Dongsi
    pivot_table_dongsi = combined.pivot_table(values=pollutant + '_dongsi', 
                                              index='hour', 
                                              aggfunc='mean')
    pivot_tables_dongsi[pollutant] = pivot_table_dongsi

# Menganalisis kapan Polutan mencapai titik tertinggi di Tiangtan dan Dongsi
for pollutant in pollutants:
    # Tiangtan
    max_tiangtan_hour = pivot_tables_tiangtan[pollutant].idxmax()
    max_tiangtan_value = pivot_tables_tiangtan[pollutant].max()
    
    # Dongsi
    max_dongsi_hour = pivot_tables_dongsi[pollutant].idxmax()
    max_dongsi_value = pivot_tables_dongsi[pollutant].max()


st.title("Visualisasi Tren Polusi Udara di Distrik Tiantan dan Dongsi, Beijing")

with st.sidebar:
    st.image("sidebarlogo.png")
    st.markdown("<h3 style='text-align:center;'>Made by Fadhil Erdya Qashmal<h3>", unsafe_allow_html=True)

# Memilih tanggal
start_date = combined['datetime'].min().date()
end_date = combined['datetime'].max().date()
selected_date = st.date_input("Pilih Tanggal", start_date, min_value=start_date, max_value=end_date)

# Mengfilter data berdasarkan tanggal yang dipilih
filtered_data = combined[combined['datetime'].dt.date == selected_date]

avg_pollution = {
    pollutant: {
        'Tiangtan': filtered_data[f'{pollutant}_tiangtan'].mean(),
        'Dongsi': filtered_data[f'{pollutant}_dongsi'].mean()
    } for pollutant in pollutants
}

# Menghitung rata-rata suhu per tahun untuk masing-masing distrik
rerata_tahunan_suhu_tiangtan = combined.groupby('year')['TEMP_tiangtan'].mean()
rerata_tahunan_suhu_dongsi = combined.groupby('year')['TEMP_dongsi'].mean()

# Membuat DataFrame untuk clustered bar chart
perbandingan_suhu_df = pd.DataFrame({
    'Year': rerata_tahunan_suhu_tiangtan.index,
    'Tiangtan': rerata_tahunan_suhu_tiangtan.values,
    'Dongsi': rerata_tahunan_suhu_dongsi.values
})


# Membuat layout tab untuk setiap polutan
tabs = st.tabs(pollutants)
for i, pollutant in enumerate(pollutants):
    with tabs[i]:
        # Visualisasi tren polusi seiring waktu dengan line plot
        st.subheader(f'Rata-rata {pollutant} pada {selected_date}:')
        col1, col2 = st.columns(2)
        fig, axs = plt.subplots(2, 1, figsize=(10, 10))
        
        with col1:
            st.metric(label='Tiangtan', value=f"{avg_pollution[pollutant]['Tiangtan']:.2f}")

        with col2:    
            st.metric(label='Dongsi', value=f"{avg_pollution[pollutant]['Dongsi']:.2f}")
        
        # Clustered bar chart
        data = pd.DataFrame({
            'District': ['Tiangtan', 'Dongsi'],
            'Average': [avg_pollution[pollutant]['Tiangtan'], avg_pollution[pollutant]['Dongsi']]
        })
        sns.barplot(x='District', y='Average', data=data, palette='muted', ax=axs[0])
        axs[0].set_title(f'Trend {pollutant} pada {selected_date}')
        axs[0].set_ylabel('Konsentrasi')
        axs[0].set_xlabel('Waktu')

        # Line plot
        sns.lineplot(data=filtered_data, x='datetime', y=f'{pollutant}_tiangtan', label='Tiangtan', ax=axs[1])
        sns.lineplot(data=filtered_data, x='datetime', y=f'{pollutant}_dongsi', label='Dongsi', ax=axs[1])
        axs[1].set_title(f'Perbandingan Rata-rata {pollutant} di Tiangtan dan Dongsi pada {selected_date}')
        axs[1].set_ylabel('Rata-rata Konsentrasi')
        axs[1].set_xlabel('Distrik')

        plt.tight_layout()
        st.pyplot(fig)  # Menampilkan plot di Streamlit
        plt.clf()  # Membersihkan figure setelah menampilkan

        st.subheader('Tingkat Fluktuasi Per Bulan')
        col1, col2 = st.columns(2)
        with col1:
            # Mengambil bulan dan tahun dari hasil tertinggi Tiangtan untuk polutan terpilih
            highest_pollution_tiangtan = monthly_avg[f'{pollutant}_tiangtan'].max()
            highest_month_tiangtan = monthly_avg.loc[monthly_avg[f'{pollutant}_tiangtan'] == highest_pollution_tiangtan, ['year', 'month']].iloc[0]
            month_tiangtan = highest_month_tiangtan['month']
            year_tiangtan = highest_month_tiangtan['year']
            st.metric(label=f"Bulan Terpolusi {pollutant} Tiangtan", value=f"{month_tiangtan}-{year_tiangtan} ({highest_pollution_tiangtan:.2f})")

        with col2:
            # Mengambil bulan dan tahun dari hasil tertinggi Dongsi untuk polutan terpilih
            highest_pollution_dongsi = monthly_avg[f'{pollutant}_dongsi'].max()
            highest_month_dongsi = monthly_avg.loc[monthly_avg[f'{pollutant}_dongsi'] == highest_pollution_dongsi, ['year', 'month']].iloc[0]
            month_dongsi = highest_month_dongsi['month']
            year_dongsi = highest_month_dongsi['year']
            st.metric(label=f"Bulan Terpolusi {pollutant} Dongsi", value=f"{month_dongsi}-{year_dongsi} ({highest_pollution_dongsi:.2f})")

        # Plotting rata-rata bulanan
        fig2, ax2 = plt.subplots(figsize=(10, 6))
        # Plotting rata-rata bulanan Tiangtan
        ax2.plot(monthly_avg['Tahun_Bulan'], monthly_avg[f'{pollutant}_tiangtan'], marker='o', label=f'{pollutant} Tiangtan')
        
        # Plotting rata-rata bulanan Dongsi
        ax2.plot(monthly_avg['Tahun_Bulan'], monthly_avg[f'{pollutant}_dongsi'], marker='x', label=f'{pollutant} Dongsi')
        
        # Konfigurasi plot
        ax2.set_title(f'Perbandingan Rata-Rata Bulanan {pollutant} antara Tiangtan dan Dongsi')
        ax2.set_xlabel('Tahun-Bulan')
        ax2.set_ylabel(f'Rata-Rata Konsentrasi {pollutant}')
        ax2.set_xticklabels(monthly_avg['Tahun_Bulan'], rotation=90)  
        ax2.legend()
        ax2.grid(True)
        st.pyplot(fig2) 

        # Metrik untuk jam tertinggi dan terendah
        st.subheader('Jam Tertinggi dan Terendah Polusi')
        col1, col2 = st.columns(2)
        
        # Tiangtan: jam tertinggi dan terendah
        max_tiangtan_hour = pivot_tables_tiangtan[pollutant].idxmax()[0]
        min_tiangtan_hour = pivot_tables_tiangtan[pollutant].idxmin()[0]
        max_tiangtan_value = pivot_tables_tiangtan[pollutant].max()[0]
        min_tiangtan_value = pivot_tables_tiangtan[pollutant].min()[0]
        
        with col1:
            st.metric(label=f'Jam Tertinggi {pollutant} Tiangtan', value=f"{max_tiangtan_hour} ({max_tiangtan_value:.2f})")
            st.metric(label=f'Jam Terendah {pollutant} Tiangtan', value=f"{min_tiangtan_hour} ({min_tiangtan_value:.2f})")
        
        # Dongsi: jam tertinggi dan terendah
        max_dongsi_hour = pivot_tables_dongsi[pollutant].idxmax()[0]
        min_dongsi_hour = pivot_tables_dongsi[pollutant].idxmin()[0]
        max_dongsi_value = pivot_tables_dongsi[pollutant].max()[0]
        min_dongsi_value = pivot_tables_dongsi[pollutant].min()[0]
        
        with col2:
            st.metric(label=f'Jam Tertinggi {pollutant} Dongsi', value=f"{max_dongsi_hour} ({max_dongsi_value:.2f})")
            st.metric(label=f'Jam Terendah {pollutant} Dongsi', value=f"{min_dongsi_hour} ({min_dongsi_value:.2f})")
        
        # Plotting rerata per jam
        st.subheader(f'Rata-rata Polusi {pollutant} per Jam')
        fig3, ax3 = plt.subplots(figsize=(10, 6))
        
        ax3.plot(pivot_tables_tiangtan[pollutant], label=f'{pollutant} Tiangtan', marker='o')
        ax3.plot(pivot_tables_dongsi[pollutant], label=f'{pollutant} Dongsi', marker='x')
        
        ax3.set_title(f'Perbandingan Rata-Rata Polusi {pollutant} per Jam antara Tiangtan dan Dongsi')
        ax3.set_xlabel('Jam')
        ax3.set_ylabel(f'Rata-Rata Konsentrasi {pollutant}')
        ax3.legend()
        ax3.grid(True)
        
        st.pyplot(fig3)  # Menampilkan plot di Streamlit

# Koordinat Tiangtan dan Dongsi
tiangtan_coords = [39.8737, 116.3975] 
dongsi_coords = [39.9289, 116.4179]  

# Fungsi untuk menentukan warna berdasarkan suhu
def get_color(value):
    if value < 5:
        return '#3186cc'  # Biru untuk suhu sangat rendah
    elif 5 <= value < 10:
        return '#66b2ff'  # Biru muda untuk suhu rendah
    elif 10 <= value < 12:
        return '#66cc99'  # Hijau muda untuk suhu sedang rendah
    elif 12 <= value < 14:
        return '#99cc66'  # Hijau kekuningan untuk suhu sedang
    elif 14 <= value < 16:
        return '#cccc66'  # Kuning untuk suhu agak tinggi
    elif 16 <= value < 18:
        return '#ffcc66'  # Oranye muda untuk suhu tinggi
    elif 18 <= value < 20:
        return '#ff9966'  # Oranye untuk suhu sangat tinggi
    else:
        return '#cc6666'  # Merah untuk suhu sangat tinggi

# Fungsi untuk membuat peta menggunakan data suhu
def create_map(year):
    # Mendapatkan data suhu rata-rata untuk tahun yang dipilih
    avg_temp_tiangtan = perbandingan_suhu_df.loc[perbandingan_suhu_df['Year'] == year, 'Tiangtan'].values[0]
    avg_temp_dongsi = perbandingan_suhu_df.loc[perbandingan_suhu_df['Year'] == year, 'Dongsi'].values[0]
    
    # Membuat peta dengan lokasi awal di sekitar Tiangtan dan Dongsi
    m = folium.Map(location=[39.9042, 116.4074], zoom_start=12)

    # Menambahkan lingkaran untuk Tiangtan dengan warna berdasarkan suhu
    folium.Circle(
        location=tiangtan_coords,
        radius=1000,  
        color='black',
        fill=True,
        fill_color=get_color(avg_temp_tiangtan),
        fill_opacity=0.6,
        popup=f"Suhu Rata-rata Tiangtan: {avg_temp_tiangtan:.2f}°C"
    ).add_to(m)

    # Menambahkan lingkaran untuk Dongsi dengan warna berdasarkan suhu
    folium.Circle(
        location=dongsi_coords,
        radius=1000,  
        color='black',
        fill=True,
        fill_color=get_color(avg_temp_dongsi),
        fill_opacity=0.6,
        popup=f"Suhu Rata-rata Dongsi: {avg_temp_dongsi:.2f}°C"
    ).add_to(m)

    # Menambahkan legenda suhu pada peta
    legend_html = """
    <div style="position: fixed;
         bottom: 50px; left: 50px; width: 200px; height: 150px;
         border:2px solid grey; z-index:9999; font-size:14px;">
         <h4 style="text-align:center;">Suhu Rata-rata</h4>
         <p style="margin:0;">&nbsp; <i style="background:#3186cc"></i>&nbsp; Suhu < 5°C</p>
         <p style="margin:0;">&nbsp; <i style="background:#66b2ff"></i>&nbsp; 5°C ≤ Suhu < 10°C</p>
         <p style="margin:0;">&nbsp; <i style="background:#66cc99"></i>&nbsp; 10°C ≤ Suhu < 12°C</p>
         <p style="margin:0;">&nbsp; <i style="background:#99cc66"></i>&nbsp; 12°C ≤ Suhu < 14°C</p>
         <p style="margin:0;">&nbsp; <i style="background:#cccc66"></i>&nbsp; 14°C ≤ Suhu < 16°C</p>
         <p style="margin:0;">&nbsp; <i style="background:#ffcc66"></i>&nbsp; 16°C ≤ Suhu < 18°C</p>
         <p style="margin:0;">&nbsp; <i style="background:#ff9966"></i>&nbsp; 18°C ≤ Suhu < 20°C</p>
         <p style="margin:0;">&nbsp; <i style="background:#cc6666"></i>&nbsp; Suhu ≥ 20°C</p>
    </div>
    """
    
    m.get_root().html.add_child(folium.Element(legend_html))

    return m


st.subheader("Perbandingan Suhu Rata-rata Tiangtan dan Dongsi")
st.write("Pilih tahun untuk melihat perbandingan suhu rata-rata antara Tiangtan dan Dongsi.")

# Data slider untuk memilih tahun
selected_year = st.slider("Pilih Tahun", min_value=2013, max_value=2016, value=2013, step=1)

# Menghasilkan peta untuk tahun yang dipilih
map_object = create_map(selected_year)
st_folium(map_object, width=700, height=500)

    

