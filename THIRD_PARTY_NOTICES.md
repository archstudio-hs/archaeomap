# 함께 쓰는 라이브러리와 자료

이 저장소의 코드와 사용 설명서는 PolyForm Strict 1.0.0을 따르지만, 아래 구성 요소와 자료는 각자의 라이선스·이용 조건을 따릅니다.
라이브러리의 라이선스 원문은 `ArchaeoMap/vendor/` 폴더에 함께 들어 있습니다.

## 라이브러리
| 이름 | 용도 | 라이선스 | 출처 |
| --- | --- | --- | --- |
| Leaflet 1.9.4 | 지도 화면 | BSD-2-Clause | https://github.com/Leaflet/Leaflet |
| Skulpt | 브라우저 안에서 유적 검색 코드(Python) 실행 | MIT | https://github.com/skulpt/skulpt |
| fflate | 유적 DB 조각(gzip) 풀기 | MIT | https://github.com/101arrowz/fflate |
| pbf | 벡터 타일 읽기 | BSD-3-Clause | https://github.com/mapbox/pbf |
| @mapbox/vector-tile | 벡터 타일 읽기 | BSD-3-Clause | https://github.com/mapbox/vector-tile-js |
| @mapbox/point-geometry | 벡터 타일 좌표 계산 | ISC | https://github.com/mapbox/point-geometry |

## 지도·고도 자료
| 자료 | 쓰는 곳 | 출처 표기·조건 |
| --- | --- | --- |
| OpenFreeMap (OpenMapTiles 스키마) | 표준·흑백·등고선 지도 | OpenFreeMap · OpenMapTiles · © OpenStreetMap contributors (ODbL) — https://openfreemap.org/ |
| Esri World Imagery | 위성 지도 | Esri, Maxar, Earthstar Geographics, and the GIS User Community. Esri 이용 약관을 따름 — https://www.esri.com/en-us/legal/terms/full-master-agreement |
| Mapzen Terrain Tiles (AWS Open Data) | 등고선·음영기복 | 원자료 기여자 — https://github.com/tilezen/joerd/blob/master/docs/attribution.md |
| Natural Earth | 나라 구분 | Public domain — https://www.naturalearthdata.com/ |

## 유적 검색 자료 (통합 유적 DB · 실시간 조회)
| 자료 | 라이선스·조건 | 출처 |
| --- | --- | --- |
| 국가유산청 국가유산포털·공간정보 | 국가유산청 공공데이터 이용 조건 | https://www.heritage.go.kr/ |
| 일본 국토수치정보(문화재 데이터) | 国土数値情報 利用規約 | https://nlftp.mlit.go.jp/ksj/ |
| UNESCO World Heritage Centre | UNESCO 공개 데이터 이용 조건 | https://data.unesco.org/explore/dataset/whc001/ |
| Wikidata | CC0 1.0 | https://www.wikidata.org/ |
| OpenStreetMap contributors / Photon | ODbL 1.0 | https://www.openstreetmap.org/copyright · https://photon.komoot.io/ |
| Pleiades | CC BY 3.0 | https://pleiades.stoa.org/credits |

통합 유적 DB(`ArchaeoMap/data/master/`)에 든 각 기록은 위 원자료의 라이선스를 그대로 따릅니다. 모은 방법은 [docs/site-db.md](docs/site-db.md)에 있습니다.
