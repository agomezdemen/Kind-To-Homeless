import "./global.css";
import React, {use, useEffect, useRef, useState} from 'react';
import { StatusBar, StyleSheet, View, ActivityIndicator, Text, Platform } from 'react-native';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { Map } from './Map';
import Header from './Header';
import Navbar from './Navbar';
import List from './List';
import Events from './Events';

export default function App() {
    const [selectedIndex, setSelectedIndex] = useState(0);
    const [selectedMarker, setSelectedMarker] = useState(null);
    const [searchQuery, setSearchQuery] = useState("");
    const [userLocation, setUserLocation] = useState(null);
    const hasTriggeredRef = useRef(false);
    const [events, setEvents] = useState({});
    useEffect(() => {
        console.log(selectedMarker);
    }, [selectedMarker]);
    const [combinedMarkers, setCombinedMarkers] = useState([]);

    useEffect(() => {
        console.log("Combined Markers Updated:", combinedMarkers);
    }, [combinedMarkers]);
    useEffect(() => {
        console.log("Search query changed:", searchQuery);
        //call functions in Map to requery with search term.
    }, [searchQuery]);



    useEffect(() => {
        const fetchEvents = async () => {
            if (
                userLocation &&
                userLocation.latitude &&
                userLocation.longitude &&
                !hasTriggeredRef.current
            ) {
                hasTriggeredRef.current = true;
                const apiHost = 'http://162.243.235.232:7544';
                const url = `${apiHost}/find_events?latitude=${userLocation.latitude}&longitude=${userLocation.longitude}`;
                console.log("Fetching events:", url);
                const resAll = `{
  "events": [
    {
      "Name": "Local Good Pantry",
      "Date": "Every Tuesday, Thursday, and Saturday",
      "Summary": "The Local Good Pantry, part of the Local Good Collective started by Chase Oaks Church, provides food assistance to the Richardson community. It partners with the City of Richardson and the North Texas Food Bank to help local residents access food and resources.",
      "Address": "741 S Sherman St, Richardson, TX 75081",
      "latitude": 32.9392,
      "longitude": -96.7294,
      "source_url": "https://localgoodpantry.org/"
    }
  ],
  "processing_time": 55.26,
  "urls_processed": 0
}`;
                setEvents(JSON.parse(resAll));
                // try {
                //     const resAll = await fetch(url);
                //     if (resAll.ok) {
                //         const data = await resAll.json();
                //         events.current = data;
                //     }
                // } catch (apiError) {
                //     console.error("Error fetching events:", apiError);
                // }
            }
        };
        fetchEvents();
    }, [userLocation]);


    return (
      <GestureHandlerRootView style={{ flex: 1 }}>
          <View className="h-full">
              <StatusBar
                  backgroundColor="black" // Or any dark color for the status bar background
                  barStyle="light-content" // This makes the icons and text white
              />
              {selectedIndex === 0 ? (
                  <View>
                      <Map setUserLocation={setUserLocation} selectedMarker={selectedMarker} setSelectedMarker={setSelectedMarker} combinedMarkers={combinedMarkers} setCombinedMarkers={setCombinedMarkers} search={searchQuery} />
                      <List markers={combinedMarkers} selectedMarker={selectedMarker} setSelectedMarker={setSelectedMarker} />
                      <Text className="text-emerald-900 text-2xl font-bold absolute top-32 left-2">Homefull</Text>
                  </View>
              ) : (
                  <Events events={events}/>
              )}
              <Header onSearchChange={setSearchQuery} />
              <Navbar selectedIndex={selectedIndex} setSelectedIndex={setSelectedIndex}  />
          </View>
      </GestureHandlerRootView>
  );
}