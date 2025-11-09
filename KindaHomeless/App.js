import "./global.css";
import React, {use, useEffect, useRef, useState} from 'react';
import { StyleSheet, View, ActivityIndicator, Text, Platform } from 'react-native';

import { Map } from './Map';
import Header from './Header';
import Navbar from './Navbar';

export default function App() {
    const [selectedIndex, setSelectedIndex] = useState(0);
    const [selectedMarker, setSelectedMarker] = useState(null);

  return (
      <View className="h-full">
          {selectedIndex === 0 ? (
              <Map selectedMarker={selectedMarker} setSelectedMarker={setSelectedMarker} />
          ) : (
              <Text className="text-white text-center mt-10">Second screen content here</Text>
          )}
          <Header />
          <Navbar selectedIndex={selectedIndex} setSelectedIndex={setSelectedIndex}  />
      </View>
  );
}