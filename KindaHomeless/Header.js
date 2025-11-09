import { SearchBar } from '@rneui/themed';
import { StyleSheet, View, ActivityIndicator, Text, Platform, Keyboard } from 'react-native';
import React, {Component} from "react";
import "./global.css";



export default class Header extends Component {
    state = {
        search: '',
    };

    componentDidMount() {
        this.keyboardDidHideListener = Keyboard.addListener('keyboardDidHide', this.handleSearchSubmit);
    }
    componentWillUnmount() {
        this.keyboardDidHideListener.remove();
    }

    updateSearch = (search) => {
        this.setState({ search });
    };

    handleSearchSubmit = () => {
        const { search } = this.state;
        if (this.props.onSearchChange) {
            this.props.onSearchChange(search.trim());
        }
    };

    render() {
        const {search} = this.state;
        return (
            <View className="h-32 w-full bg-emerald-900  border-b-emerald-400 border-b-2 absolute pt-12 p-4">
                <SearchBar
                    placeholder="Search points of interest..."
                    onChangeText={this.updateSearch}
                    onSubmitEditing={this.handleSearchSubmit}
                    returnKeyType="search"
                    value={search}
                    platform="android"
                    containerStyle={{"backgroundColor":"transparent"}}
                    inputStyle={{marginLeft:"0"}}
                    inputContainerStyle={{
                        "borderRadius": 30,
                        "backgroundColor": "ivory"
                    }}
                        ></SearchBar>
            </View>
        );
    }
}
