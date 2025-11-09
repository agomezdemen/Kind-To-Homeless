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