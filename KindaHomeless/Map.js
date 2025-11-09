import React, {useEffect, useRef, useState} from 'react';
import MapView, { Marker, Callout } from 'react-native-maps';
import { StyleSheet, View, ActivityIndicator, Text, Platform, useColorScheme } from 'react-native';
import * as Location from 'expo-location';

export function Map({ selectedMarker, setSelectedMarker }) {
  const mapRef = useRef(null);
  const [region, setRegion] = useState(null);
  const [yourLocation, setYourLocation] = useState(null);
  const [foodMarkers, setFoodMarkers] = useState([]);
  const [shelterMarkers, setShelterMarkers] = useState([]);
  const [showerMarkers, setShowerMarkers] = useState([]);
  const [toiletMarkers, setToiletMarkers] = useState([]);
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
        // Toilets: tan markers, Showers: Blue Markers, Food: Yellow Markers, Shelters: Green Markers
        // toilets","shower","drinking_water","water_tap","place_of_worship","social_facility","shelter","soup_kitchen","food_bank","clothing_bank","outreach","homeless_services","laundry","day_care","community_centre","social_centre","welfare"
        const apiHost = 'http://162.243.235.232:7544'
        const radiusMiles = 5;
        const url = `${apiHost}/nearby?latitude=${latitude}&longitude=${longitude}&radius=${radiusMiles}`;
        try {
          setLoading(true);
          // fetch toilets
          const resToilets = await fetch(`${url}&features=toilets`);
          if (resToilets.ok) {
            const toiletData = await resToilets.json();
            setToiletMarkers(toiletData.results.map((item, index) => ({
              id: `toilet-${index}`,
              title: item.name,
              description: item.description,
              latitude: item.latitude,
              longitude: item.longitude,
            })));
            console.log("Toilet data fetched:", toiletData);
          }
          // fetch showers
          const resShowers = await fetch(`${url}&features=showers`);
          if (resShowers.ok) {
            const showerData = await resShowers.json();
            setShowerMarkers(showerData.results.map((item, index) => ({
              id: `shower-${index}`,
              title: item.name,
              description: item.description,
              latitude: item.latitude,
              longitude: item.longitude,
            })));
            console.log("Shower data fetched:", showerData);
          }
          // fetch food
          const resFood = await fetch(`${url}&features=food`);
          if (resFood.ok) {
            const foodData = await resFood.json();
            setFoodMarkers(foodData.results.map((item, index) => ({
              id: `food-${index}`,
              title: item.name,
              description: item.description,
              latitude: item.latitude,
              longitude: item.longitude,
            })));
            console.log("Food data fetched:", foodData);
          }
          // fetch shelters
          const resShelters = await fetch(`${url}&features=shelters`);
          if (resShelters.ok) {
            const shelterData = await resShelters.json();
            setShelterMarkers(shelterData.results.map((item, index) => ({
              id: `shelter-${index}`,
              title: item.name,
              description: item.description,
              latitude: item.latitude,
              longitude: item.longitude,
            })));
            console.log("Shelter data fetched:", shelterData);
          }
          setLoading(false);
        } catch (apiError) {
          console.error('Error fetching nearby data:', apiError);
        }
        
        
        const yourMarker = {
          id: 'you-1',
          title: 'You are here',
          description: 'Current Location',
          latitude,
          longitude,
        };
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
      >
          {yourLocation && (
            <Marker
              key={yourLocation.id}
              coordinate={{ latitude: yourLocation.latitude, longitude: yourLocation.longitude }}
              //pinColor='blue'
              onPress={() => setSelectedMarker(yourLocation)}
            >
            
            </Marker>
          )}
        {shelterMarkers.map((marker) => (
          <Marker
            key={marker.id}
            coordinate={{ latitude: marker.latitude, longitude: marker.longitude }}
            pinColor='green'
            onPress={() => setSelectedMarker(marker)}
          />
        ))}
        {showerMarkers.map((marker) => (
          <Marker
            key={marker.id}
            coordinate={{ latitude: marker.latitude, longitude: marker.longitude }}
            pinColor='blue'
            onPress={() => setSelectedMarker(marker)}
          />
        ))}
        {foodMarkers.map((marker) => (
          <Marker
            key={marker.id}
            coordinate={{ latitude: marker.latitude, longitude: marker.longitude }}
            pinColor='yellow'
            onPress={() => setSelectedMarker(marker)}
          />
        ))}
        {toiletMarkers.map((marker) => (
          <Marker
            key={marker.id}
            coordinate={{ latitude: marker.latitude, longitude: marker.longitude }}
            pinColor='tan'
            onPress={() => setSelectedMarker(marker)}
          />
        ))}
      </MapView>
    </View>
  );
}