import "./global.css";
import React, {useEffect, useRef, useState} from 'react';
import { StyleSheet, View, ActivityIndicator, Text, Platform } from 'react-native';

import { Map } from './Map';
import Header from './Header';

export default function App() {
  return (
      <View>
          <Map />
          <Header />
      </View>
  );
}