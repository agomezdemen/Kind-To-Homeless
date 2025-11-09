import React, {useEffect, useRef, useState} from 'react';
import MapView, { Marker, Callout } from 'react-native-maps';
import { StyleSheet, View, ActivityIndicator, Text, Platform, useColorScheme } from 'react-native';
import * as Location from 'expo-location';

export function Map({ selectedMarker, setSelectedMarker, combinedMarkers, setCombinedMarkers }) {
  const mapRef = useRef(null);
  const [region, setRegion] = useState(null);
  const [yourLocation, setYourLocation] = useState(null);
  const [foodMarkers, setFoodMarkers] = useState([]);
  const [shelterMarkers, setShelterMarkers] = useState([]);
  const [showerMarkers, setShowerMarkers] = useState([]);
  const [toiletMarkers, setToiletMarkers] = useState([]);
  const [drinkingWaterMarkers, setDrinkingWaterMarkers] = useState([]); // aqua
  const [clothesMarkers, setClothesMarkers] = useState([]); // purple
  // const [placeOfWorshipMarkers, setPlaceOfWorshipMarkers] = useState([]); // plum
  const [welfareMarkers, setWelfareMarkers] = useState([]); // navy
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
          // fetch toilets
          const resToilets = await fetch(`${url}&feature=toilets`);
          //console.log("Fetching toilets from:", `${url}&feature=toilets`);
          if (resToilets.ok) {
            const toiletData = await resToilets.json();
            if(toiletData !== undefined && toiletData.results){
              setToiletMarkers(toiletData.results.map((item, index) => ({
                id: `toilet-${index}`,
                name: item.name,
                description: item.description,
                latitude: item.latitude,
                longitude: item.longitude,
              })));
            }
            console.log("Toilet data fetched:", toiletData);
          }
          // fetch showers
          const resShowers = await fetch(`${url}&feature=shower`);
          if (resShowers.ok) {
            const showerData = await resShowers.json();
            if(showerData !== undefined && showerData.results){
              setShowerMarkers(showerData.results.map((item, index) => ({
                id: `shower-${index}`,
                name: item.name,
                description: item.description,
                latitude: item.latitude,
                longitude: item.longitude,
              })));
            }
            console.log("Shower data fetched:", showerData);
          }
          // fetch food
          const resFood = await fetch(`${url}&feature=food_bank`);
          if (resFood.ok) {
            const foodData = await resFood.json();
            if(foodData !== undefined && foodData.results){
              setFoodMarkers(foodData.results.map((item, index) => ({
                id: `food-${index}`,
                name: item.name,
                description: item.description,
                latitude: item.latitude,
                longitude: item.longitude,
              })));
            }
            console.log("Food data fetched:", foodData);
          }
          const resSoupKitchens = await fetch(`${url}&feature=soup_kitchen`);
          if (resSoupKitchens.ok) {
            const soupKitchenData = await resSoupKitchens.json();
            if(soupKitchenData !== undefined && soupKitchenData.results){
              setFoodMarkers(prev => [...prev, ...soupKitchenData.results.map((item, index) => ({
                id: `soup_kitchen-${index}`,
                name: item.name,
                description: item.description,
                latitude: item.latitude,
                longitude: item.longitude,
              }))]);
            }
            console.log("Soup Kitchen data fetched:", soupKitchenData);
          }
          // const resSocialcenters = await fetch(`${url}&feature=social_centre`);
          // if (resSocialcenters.ok) {
          //   const socialcenterData = await resSocialcenters.json();
          //   if(socialcenterData !== undefined && socialcenterData.results){
          //     setShelterMarkers(prev => [...prev, ...socialcenterData.results.map((item, index) => ({
          //       id: `social_centre-${index}`,
          //       name: item.name,
          //       description: item.description,
          //       latitude: item.latitude,
          //       longitude: item.longitude,
          //     }))]);
          //   }
          // }
          const resSocialFacility = await fetch(`${url}&feature=social_facility`);
          if (resSocialFacility.ok) {
            const socialFacilityData = await resSocialFacility.json();
            if(socialFacilityData !== undefined && socialFacilityData.results){
              setShelterMarkers(prev => [...prev, ...socialFacilityData.results.map((item, index) => ({
                id: `social_facility-${index+1}`,
                name: item.name,
                description: item.description,
                latitude: item.latitude,
                longitude: item.longitude,
              }))]);
            }
            console.log("Social Facility data fetched:", socialFacilityData);
          }
          
          const resHomelessServices = await fetch(`${url}&feature=homeless_services`);
          if (resHomelessServices.ok) {
            const homelessServicesData = await resHomelessServices.json();
            if(homelessServicesData !== undefined && homelessServicesData.results){
              setShelterMarkers(prev => [...prev, ...homelessServicesData.results.map((item, index) => ({
                id: `homeless_services-${index}`,
                name: item.name,
                description: item.description,
                latitude: item.latitude,
                longitude: item.longitude,
              }))]);
            }
            console.log("Homeless Services data fetched:", homelessServicesData);
          }
          
          const resDrinkingWater = await fetch(`${url}&feature=drinking_water`);
          if (resDrinkingWater.ok) {
            const drinkingWaterData = await resDrinkingWater.json();
            if(drinkingWaterData !== undefined && drinkingWaterData.results){
              setDrinkingWaterMarkers(drinkingWaterData.results.map((item, index) => ({
                id: `drinking_water-${index}`,
                name: item.name,
                description: item.description,
                latitude: item.latitude,
                longitude: item.longitude,
              })));
            }
             console.log("Drinking Water data fetched:", drinkingWaterData);
          }
        
          const resWaterTaps = await fetch(`${url}&feature=water_tap`);
          if (resWaterTaps.ok) {
            const waterTapData = await resWaterTaps.json();
            if(waterTapData !== undefined && waterTapData.results){
              setDrinkingWaterMarkers(prev => [...prev, ...waterTapData.results.map((item, index) => ({
                id: `water_tap-${index}`,
                name: item.name,
                description: item.description,
                latitude: item.latitude,
                longitude: item.longitude,
              }))]);
            }
            console.log("Water Tap data fetched:", waterTapData);
          }
          
          const resClothingBanks = await fetch(`${url}&feature=clothing_bank`);
          if (resClothingBanks.ok) {
            const clothingBankData = await resClothingBanks.json();
            if(clothingBankData !== undefined && clothingBankData.results){
              setClothesMarkers(clothingBankData.results.map((item, index) => ({
                id: `clothing_bank-${index}`,
                name: item.name,
                description: item.description,
                latitude: item.latitude,
                longitude: item.longitude,
              })));
            }
          console.log("Clothing Bank data fetched:", clothingBankData);
          }
          
          const resLaundries = await fetch(`${url}&feature=laundry`);
          if (resLaundries.ok) {
            const laundryData = await resLaundries.json();
            if(laundryData !== undefined && laundryData.results){
              setClothesMarkers(prev => [...prev, ...laundryData.results.map((item, index) => ({
                id: `laundry-${index}`,
                name: item.name,
                description: item.description,
                latitude: item.latitude,
                longitude: item.longitude,
              }))]);
            }
            console.log("Laundry data fetched:", laundryData);
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
          const resWelfare = await fetch(`${url}&feature=welfare`);
          if (resWelfare.ok) {
            const welfareData = await resWelfare.json();
            if(welfareData !== undefined && welfareData.results){
              setWelfareMarkers(welfareData.results.map((item, index) => ({
                id: `welfare-${index}`,
                name: item.name,
                description: item.description,
                latitude: item.latitude,
                longitude: item.longitude,
              })));
            }
            console.log("Welfare data fetched:", welfareData);
          }
          
          const resOutreach = await fetch(`${url}&feature=outreach`);
          if (resOutreach.ok) {
            const outreachData = await resOutreach.json();
            if(outreachData !== undefined && outreachData.results){
              setWelfareMarkers(prev => [...prev, ...outreachData.results.map((item, index) => ({
                id: `outreach-${index}`,
                name: item.name,
                description: item.description,
                latitude: item.latitude,
                longitude: item.longitude,
              }))]);
            }
            console.log("Outreach data fetched:", outreachData);
          }
          
          const resAll = await fetch(`${url}&feature=all`);
          if (resAll.ok) {
            const allData = await resAll.json();
            if(allData !== undefined && allData.results){
              setCombinedMarkers(allData.results.map((item, index) => ({
                id: `all-${index}`,
                name: item.name,
                feature_type: item.description,
                latitude: item.latitude,
                longitude: item.longitude,
                distance: item.distance,
                address: item.address
              })));
            }
          }
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
        {drinkingWaterMarkers.map((marker) => (
          <Marker
            key={marker.id}
            coordinate={{ latitude: marker.latitude, longitude: marker.longitude }}
            pinColor='aqua'
            onPress={() => setSelectedMarker(marker)}
          />
        ))}
        {clothesMarkers.map((marker) => (
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
        {welfareMarkers.map((marker) => (
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