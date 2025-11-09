import React, {useEffect, useRef, useState} from 'react';
import MapView, { Marker, Callout } from 'react-native-maps';
import { StyleSheet, View, ActivityIndicator, Text, Platform, useColorScheme } from 'react-native';
import * as Location from 'expo-location';

export function Map({ selectedMarker, setSelectedMarker, combinedMarkers, setCombinedMarkers }) {
  const mapRef = useRef(null);
  const [region, setRegion] = useState(null);
  const [yourLocation, setYourLocation] = useState(null);

  // const [placeOfWorshipMarkers, setPlaceOfWorshipMarkers] = useState([]); // plum
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
          
          // const resPlaceOfWorship = await fetch(`${url}&feature=place_of_worship`);
          // if (resPlaceOfWorship.ok) {
          //   const placeOfWorshipData = await resPlaceOfWorship.json();
          //   if(placeOfWorshipData !== undefined && placeOfWorshipData.results){
          //     setPlaceOfWorshipMarkers(placeOfWorshipData.results.map((item, index) => ({
          //       id: `place_of_worship-${index}`,
          //       name: item.name,
          //       description: item.description,
          //       latitude: item.latitude,
          //       longitude: item.longitude,
          //     })));
          //   }
          // }
        } catch (apiError) {
          console.error('Error fetching nearby data:', apiError);
        }

        const yourMarker = {
          id: 'you-1',
          name: 'You are here',
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
        {combinedMarkers.filter(marker=>
        marker.feature_type==="social_centre" ||
        marker.feature_type==="social_facility" ||
        marker.feature_type==="homeless_services"
        ).map((marker) => (
          <Marker
            key={marker.id}
            coordinate={{ latitude: marker.latitude, longitude: marker.longitude }}
            pinColor='green'
            onPress={() => setSelectedMarker(marker)}
          />
        ))}
        {combinedMarkers.filter((marker)=>marker.feature_type === "shower").map((marker) => (
          <Marker
            key={marker.id}
            coordinate={{ latitude: marker.latitude, longitude: marker.longitude }}
            pinColor='blue'
            onPress={() => setSelectedMarker(marker)}
          />
        ))}
        {combinedMarkers.filter(marker=>
        marker.feature_type=== "food_bank" ||
        marker.feature_type==="soup_kitchen"
        ).map((marker) => (
          <Marker
            key={marker.id}
            coordinate={{ latitude: marker.latitude, longitude: marker.longitude }}
            pinColor='yellow'
            onPress={() => setSelectedMarker(marker)}
          />
        ))}
        {combinedMarkers.filter((marker)=>(marker.feature_type === "toilets")).map((marker) => (
          <Marker
            key={marker.id}
            coordinate={{ latitude: marker.latitude, longitude: marker.longitude }}
            pinColor='tan'
            onPress={() => setSelectedMarker(marker)}
          />
        ))}
        {combinedMarkers.filter(marker=>
        marker.feature_type==="drinking_water" ||
        marker.feature_type==="water_tap"
        ).map((marker) => (
          <Marker
            key={marker.id}
            coordinate={{ latitude: marker.latitude, longitude: marker.longitude }}
            pinColor='aqua'
            onPress={() => setSelectedMarker(marker)}
          />
        ))}
        {combinedMarkers.filter(marker=>
        marker.feature_type==="clothing_bank"|| 
        marker.feature_type==="laundry"
        ).map((marker) => (
          <Marker
            key={marker.id}
            coordinate={{ latitude: marker.latitude, longitude: marker.longitude }}
            pinColor='purple'
            onPress={() => setSelectedMarker(marker)}
          />
        ))}
        {/* {placeOfWorshipMarkers.map((marker) => (
          <Marker
            key={marker.id}
            coordinate={{ latitude: marker.latitude, longitude: marker.longitude }}
            pinColor='plum'
            onPress={() => setSelectedMarker(marker)}
          />
        ))} */}
        {combinedMarkers.filter(marker=>
        marker.feature_type==="welfare"||
        marker.feature_type==="outreach"
        ).map((marker) => (
          <Marker
            key={marker.id}
            coordinate={{ latitude: marker.latitude, longitude: marker.longitude }}
            pinColor='navy'
            onPress={() => setSelectedMarker(marker)}
          />
        ))}
      </MapView>
    </View>
  );
}