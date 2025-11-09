import "./global.css";
import React, {useEffect, useRef, useState} from 'react';
import { StyleSheet, View, ActivityIndicator, Text, Platform } from 'react-native';

import { Map } from './Map';
import Header from './Header';
import Navbar from './Navbar';

export default function App() {

  return (
      <View className="h-full">
          <Map />
          <Header />
          <Navbar />
      </View>
  );
}