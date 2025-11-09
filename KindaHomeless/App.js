import React, {useEffect, useRef, useState} from 'react';
import MapView, { Marker, Callout } from 'react-native-maps';
import { StyleSheet, View, ActivityIndicator, Text, Platform } from 'react-native';
import * as Location from 'expo-location';
  
export default function App() {
  const mapRef = useRef(null);
  const [region, setRegion] = useState(null);
  const [markers, setMarkers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

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
        setMarkers([yourMarker]); // Temporarily just show user location as marker
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

  const handleMapPress = (e) => {
    const { latitude, longitude } = e.nativeEvent.coordinate;
    if(markers.contains(m => m.latitude === latitude && m.longitude === longitude)) {
      markers.at(markers.findIndex(m => m.latitude === latitude && m.longitude === longitude)).description = "pin check";
    }
    //const id = String(Date.now());
    //setMarkers((prev) => [...prev, { id, title: 'Pinned', description: 'User placed', latitude, longitude }]);
  };

  if (loading) { // Grayson do your UI magic here for the loading state
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" />
        <Text style={{ marginTop: 8 }}>Getting location and fetching nearby data…</Text>
      </View>
    ); 
  }

  if (error) {
    return ( // Grayson do your UI magic here for when they deny location permission or other errors
      <View style={styles.center}>
        <Text>{error}</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      
      <MapView
        ref={mapRef}
        style={styles.map}
        initialRegion={region}
        onPress={handleMapPress}
      >
        {markers.map((m) => (
          <Marker
            key={m.id}
            coordinate={{ latitude: m.latitude, longitude: m.longitude }}
          >
            <Callout>
              <View style={{ width: 180 }}>
                <Text style={{ fontWeight: '600' }}>{m.title}</Text>
                <Text>{m.description}</Text>
                <Text style={{ color: '#666', marginTop: 6 }}>{m.latitude.toFixed(5)}, {m.longitude.toFixed(5)}</Text>
              </View>
            </Callout>
          </Marker>
        ))}
      </MapView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  map: {
    width: '100%',
    height: '100%',
  },
});
