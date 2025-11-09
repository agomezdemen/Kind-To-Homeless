import React, {useEffect, useRef, useState} from 'react';
import MapView, { Marker, Callout } from 'react-native-maps';
import { StyleSheet, View, ActivityIndicator, Text, Platform } from 'react-native';
import * as Location from 'expo-location';
import { Map } from './Map';
export default function App() {
  return <Map />;
}