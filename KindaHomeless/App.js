import "./global.css";
import React, {use, useEffect, useRef, useState} from 'react';
import { StatusBar, StyleSheet, View, ActivityIndicator, Text, Platform } from 'react-native';

import { Map } from './Map';
import Header from './Header';
import Navbar from './Navbar';

export default function App() {
    const [selectedIndex, setSelectedIndex] = useState(0);
    const [selectedMarker, setSelectedMarker] = useState(null);
    const [combinedMarkers, setCombinedMarkers] = useState([]);
    useEffect(() => {
        (async () => {
          
            // Determine API base host. On Android emulator use 10.0.2.2 to reach host machine. 
            // Toilets: tan markers, Showers: Blue Markers, Food: Yellow Markers, Shelters: Green Markers
            // "place_of_worship","outreach","welfare"
            const apiHost = 'http://162.243.235.232:7544'
            const radiusMiles = 3;
            const url = `${apiHost}/nearby?latitude=${latitude}&longitude=${longitude}&radius=${radiusMiles}`;
            try {
    
              const resAll = await fetch(`${url}`);
              if (resAll.ok) {
                const allData = await resAll.json();
                if(allData !== undefined && allData.results){
                  setCombinedMarkers(allData.results.map((item, index) => ({
                    id: `all-${index}`,
                    name: item.name,
                    feature_type: item.feature_type,
                    latitude: item.latitude,
                    longitude: item.longitude,
                    distance: item.distance,
                    address: item.address
                  })));
                }
                console.log(allData)
              }          
              
            } catch (apiError) {
              console.error('Error fetching nearby data:', apiError);
            }})})
    useEffect(() => {
        console.log("Combined Markers Updated:", combinedMarkers);
    }, [combinedMarkers]);
  return (
      <View className="h-full">
          <StatusBar
              backgroundColor="black" // Or any dark color for the status bar background
              barStyle="light-content" // This makes the icons and text white
          />
          {selectedIndex === 0 ? (
              <View>
                <Map selectedMarker={selectedMarker} setSelectedMarker={setSelectedMarker} combinedMarkers={combinedMarkers} setCombinedMarkers={setCombinedMarkers} />
                <Text className="text-emerald-900 text-2xl font-bold absolute top-32 left-2">♥︎ Kind To Homeless</Text>
              </View>
          ) : (
              <Text className="text-white text-center mt-10">Second screen content here</Text>
          )}
          <Header />
          <Navbar selectedIndex={selectedIndex} setSelectedIndex={setSelectedIndex}  />
      </View>
  );
}