import React, {useEffect, useRef, useState} from 'react';
import MapView, { Marker, Callout } from 'react-native-maps';
import { StyleSheet, View, ActivityIndicator, Text, Platform, useColorScheme } from 'react-native';
import * as Location from 'expo-location';

export function Map() {
  const mapRef = useRef(null);
  const [region, setRegion] = useState(null);
  const [yourLocation, setYourLocation] = useState(null);
  const [foodMarkers, setFoodMarkers] = useState([]);
  const [shelterMarkers, setShelterMarkers] = useState([]);
  const [showerMarkers, setShowerMarkers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedMarker, setSelectedMarker] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        const { status } = await Location.requestForegroundPermissionsAsync(); // get location permission
        if (status !== 'granted') {
          setError('Location permission denied');
          setLoading(false);
          return;
        }

        const loc = await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.Highest });
        const { latitude, longitude } = loc.coords;

        const initialRegion = {
          latitude,
          longitude,
          latitudeDelta: 0.01,
          longitudeDelta: 0.01,
        };

        setRegion(initialRegion);

        // Determine API base host. On Android emulator use 10.0.2.2 to reach host machine. 
        // Toilets: Brown markers, Showers: Blue Markers, Food: Yellow Markers, Shelters: Green Markers
        /*const apiHost = Platform.OS === 'android' ? 'http://10.0.2.2:8000' : 'http://127.0.0.1:8000';
        const url = `${apiHost}/nearby?lat=${latitude}&lon=${longitude}&radius=1`;

        const res = await fetch(url);
        if (!res.ok) throw new Error(`API error: ${res.status}`);
        const data = await res.json();

        // The API currently echoes the provided lat/lon; create a single marker from it.
        const apiMarker = { // I'll change this later to reflect real API data
          id: 'api-1',
          title: 'API Nearby',
          description: `radius: ${data.radius_miles}`,
          latitude: data.latitude,
          longitude: data.longitude,
        };
        setMarkers([apiMarker]);*/
        const yourMarker = {
          id: 'you-1',
          title: 'You are here',
          description: 'Current Location',
          latitude,
          longitude,
        };
        const foodSample = {
          id: 'food-1',
          title: 'food',
          description: 'test food marker',
          latitude: latitude + 0.0005,
          longitude: longitude + 0.0005,
        };
        setFoodMarkers([foodSample]);
        setYourLocation(yourMarker); // Temporarily just show user location as marker
        // Auto-zoom tighter around user
        const zoomRegion = { ...initialRegion, latitudeDelta: 0.004, longitudeDelta: 0.004 };
        setTimeout(() => {
          if (mapRef.current && mapRef.current.animateToRegion) {
            mapRef.current.animateToRegion(zoomRegion, 800);
          }
        }, 300);
      } catch (e) {
        setError(String(e));
      } finally {
        setLoading(false);
      }
    })();
  }, []);


  const handleMapPress = (e) => {// replace the Pin text thing with eleven labs api call later
    const { latitude, longitude } = e.nativeEvent.coordinate;
    if(foodMarkers.includes(m => m.latitude === latitude && m.longitude === longitude)) {
      const select = foodMarkers.at(foodMarkers.findIndex(m => m.latitude === latitude && m.longitude === longitude))
      //add request to eleven labs here
      setSelectedMarker(select);
    } else if(shelterMarkers.includes(m => m.latitude === latitude && m.longitude === longitude)) {
      const select = shelterMarkers.at(shelterMarkers.findIndex(m => m.latitude === latitude && m.longitude === longitude))
      //add request to eleven labs here
      setSelectedMarker(select);
    } else if(showerMarkers.includes(m => m.latitude === latitude && m.longitude === longitude)) {
      const select = showerMarkers.at(showerMarkers.findIndex(m => m.latitude === latitude && m.longitude === longitude))
      //add request to eleven labs here
      setSelectedMarker(select);
    } else if(yourLocation && yourLocation.latitude === latitude && yourLocation.longitude === longitude) {
      //add request to eleven labs here
      setSelectedMarker(yourLocation);
    }
    //const id = String(Date.now());
    //setMarkers((prev) => [...prev, { id, title: 'Pinned', description: 'User placed', latitude, longitude }]);
  };

  if (loading) { // Grayson do your UI magic here for the loading state
    return (
      <View /*style={}*/>
        <ActivityIndicator size="large" />
        <Text /*style={{ marginTop: 8 }}*/>Getting location and fetching nearby data…</Text>
      </View>
    ); 
  }

  if (error) {
    return ( // Grayson do your UI magic here for when they deny location permission or other errors
      <View /*style={styles.center}*/>
        <Text>{error}</Text>
      </View>
    );
  }

  return (
    <View /*style={styles.container}*/>
      
      <MapView
        ref={mapRef}
        style={{width: '100%', height: '100%'}}
        initialRegion={region}
        onPress={handleMapPress}
      >
          {yourLocation && (
            <Marker
              key={yourLocation.id}
              coordinate={{ latitude: yourLocation.latitude, longitude: yourLocation.longitude }}
              //pinColor='blue'
            >
            
            </Marker>
          )}
        {shelterMarkers.map((marker) => (
          <Marker
            key={marker.id}
            coordinate={{ latitude: marker.latitude, longitude: marker.longitude }}
            pinColor='green'
          />
        ))}
        {showerMarkers.map((marker) => (
          <Marker
            key={marker.id}
            coordinate={{ latitude: marker.latitude, longitude: marker.longitude }}
            pinColor='blue'
          />
        ))}
        {foodMarkers.map((marker) => (
          <Marker
            key={marker.id}
            coordinate={{ latitude: marker.latitude, longitude: marker.longitude }}
            pinColor='yellow'
          />
        ))}
      </MapView>
    </View>
  );
}