''' This is a set of tests for the cells.py module.
    See conftest.py for details on the test fixtures used.
'''

from collections import OrderedDict
from pkg_resources import resource_filename

import pytest

from conductor.cells import *
from conductor.snbparams import load_snb_parms, PaddedDeque, front_padding
from conductor.vegparams import load_veg_parms

GLACIER_ID = Band.glacier_id
OPEN_GROUND_ID = Band.open_ground_id


@pytest.mark.incremental
class TestsSimpleUnit:
    def test_band_and_hru_units(self, simple_unit_test_parms, large_merge_cells_unit_test_parms):

        test_median_elevs_simple, test_median_elevs, test_area_fracs_simple, test_area_fracs, \
            test_area_fracs_by_band, test_veg_types, expected_num_hrus, expected_root_zone_parms \
            = simple_unit_test_parms

        elevation_cells, hru_cells, expected_zs, expected_afs = large_merge_cells_unit_test_parms

        def test_band_simple(self):
            my_band = Band(test_median_elevs_simple[0])

            assert my_band.median_elev == test_median_elevs_simple[0]
            assert my_band.area_frac == 0
            assert my_band.area_frac_glacier == 0
            assert my_band.area_frac_non_glacier == 0
            assert my_band.area_frac_open_ground == 0
            assert my_band.hrus == {}
            assert my_band.num_hrus == 0

        def test_hru_simple(self):
            my_hru = HydroResponseUnit(test_area_fracs_simple[0], expected_root_zone_parms['22'])    

            assert my_hru.area_frac == test_area_fracs_simple[0]
            assert my_hru.root_zone_parms == expected_root_zone_parms['22']
            
        def test_band_typical(self):
            my_band = Band(test_median_elevs_simple[0])

            # Create and populate three HRUs in this Band...
            for veg_type, area_frac, root_zone in zip(test_veg_types, test_area_fracs_simple, expected_root_zone_parms):
                my_band.hrus[veg_type] = HydroResponseUnit(area_frac, root_zone)

            assert my_band.median_elev == test_median_elevs_simple[0]
            assert my_band.area_frac == sum(test_area_fracs_simple[0:3])
            assert my_band.area_frac_glacier == test_area_fracs_simple[2]
            assert my_band.area_frac_non_glacier == sum(test_area_fracs_simple[0:3]) - test_area_fracs_simple[2]
            assert my_band.area_frac_open_ground == test_area_fracs_simple[1]
            assert my_band.num_hrus == 3
            for veg, afrac, rzone in zip(test_veg_types, test_area_fracs_simple, expected_root_zone_parms):
                assert my_band.hrus[veg].area_frac == afrac
                assert my_band.hrus[veg].root_zone_parms == rzone

        # Load up data from large sample vegetation and snow band parameters files and test a few pieces
        # of the cells created
        def test_merge_cell_input(self):
            cells = merge_cell_input(hru_cells, elevation_cells)
            assert len(cells) == 6
            assert len(cells['369560']) == 11
            zs = [ band.median_elev for band in cells['368470'] ]
            assert zs == expected_zs
            afs = { band.hrus[19].area_frac for band in cells['368470'] if 19 in band.hrus }
            assert afs == expected_afs
            assert cells['368470'][0].num_hrus == 2

    def test_cell_creation_simple(self, simple_unit_test_parms, toy_domain_64px_cells):
        """Load up the toy problem domain from snow band and vegetation parameter files
        and thoroughly check (against simple unit test parms, which should also partially
        represent the toy domain) that the cells were created correctly"""

        test_median_elevs_simple, test_median_elevs, test_area_fracs_simple, test_area_fracs, \
            test_area_fracs_by_band, test_veg_types, expected_num_hrus, expected_root_zone_parms \
            = simple_unit_test_parms

        cells, cell_ids, num_snow_bands, band_size, expected_band_ids, expected_root_zone_parms = toy_domain_64px_cells

        # Test that the correct number of Cells were instantiated
        assert len(cells) == 2
        # Test that the correct number of Bands was instantiated for each cell
        assert len(cells[cell_ids[0]]) == 4
        assert len(cells[cell_ids[1]]) == 3
        # Test that the left and right padding is accounted for
        assert cells[cell_ids[0]].left_padding == 0
        assert cells[cell_ids[0]].right_padding == 1
        assert cells[cell_ids[1]].left_padding == 1
        assert cells[cell_ids[1]].right_padding == 1

        # Test that area fractions and root zone parameters for each HRU in each band of one cell are correct
        assert cells[cell_ids[0]][0].hrus[11].area_frac == test_area_fracs[cell_ids[0]][0]
        assert cells[cell_ids[0]][0].hrus[19].area_frac == test_area_fracs[cell_ids[0]][1]
        assert cells[cell_ids[0]][1].hrus[11].area_frac == test_area_fracs[cell_ids[0]][2]
        assert cells[cell_ids[0]][1].hrus[19].area_frac == test_area_fracs[cell_ids[0]][3]
        assert cells[cell_ids[0]][1].hrus[22].area_frac == test_area_fracs[cell_ids[0]][4]
        assert cells[cell_ids[0]][2].hrus[19].area_frac == test_area_fracs[cell_ids[0]][5]
        assert cells[cell_ids[0]][2].hrus[22].area_frac == test_area_fracs[cell_ids[0]][6]
        assert cells[cell_ids[0]][3].hrus[19].area_frac == test_area_fracs[cell_ids[0]][7]

        assert cells[cell_ids[0]][0].hrus[11].root_zone_parms == expected_root_zone_parms['11']
        assert cells[cell_ids[0]][0].hrus[19].root_zone_parms == expected_root_zone_parms['19']
        assert cells[cell_ids[0]][1].hrus[11].root_zone_parms == expected_root_zone_parms['11']
        assert cells[cell_ids[0]][1].hrus[19].root_zone_parms == expected_root_zone_parms['19']
        assert cells[cell_ids[0]][1].hrus[22].root_zone_parms == expected_root_zone_parms['22']
        assert cells[cell_ids[0]][2].hrus[19].root_zone_parms == expected_root_zone_parms['19']
        assert cells[cell_ids[0]][2].hrus[22].root_zone_parms == expected_root_zone_parms['22']
        assert cells[cell_ids[0]][3].hrus[19].root_zone_parms == expected_root_zone_parms['19']

        for band_id in expected_band_ids[cell_ids[0]]:
            # Test that the number of HRUs reported for each Band in one cell is correct
            assert cells[cell_ids[0]][band_id].num_hrus == expected_num_hrus[cell_ids[0]][band_id]
            # Test that all HRU area fractions within a Band add up to original input
            assert sum(hru.area_frac for hru in cells[cell_ids[0]][band_id].hrus.values()) == sum(test_area_fracs_by_band[cell_ids[0]][str(band_id)])

@pytest.mark.incremental
class TestsDynamic:
    def test_cells_dynamic(self, toy_domain_64px_cells):

        cells, cell_ids, num_snow_bands, band_size, expected_band_ids, expected_root_zone_parms = toy_domain_64px_cells

        def test_existing_glacier_growth_within_band_replacing_all_open_ground():
            """test_cells_dynamic -- Test #1: Simulates glacier expansion over all open ground in Band 2 """
            new_glacier_area_frac = 0.1875 # 12/64 pixels in toy problem domain, 12/12 pixels for Band 2
            # Glacier HRU area fraction change:
            cells[cell_ids[0]][2].hrus[22].area_frac = new_glacier_area_frac
            # open ground HRU is now gone:
            new_open_ground_area_frac = 0 # not used
            cells[cell_ids[0]][2].delete_hru(OPEN_GROUND_ID)
            # Check that there is only one HRU left in this band
            assert cells[cell_ids[0]][2].num_hrus == 1

        def test_new_glacier_growth_into_band_and_replacing_all_open_ground():
            """test_cells_dynamic -- Test #2: Simulates glacier expansion to replace all open ground in Band 3 (HRU delete + create)"""
            new_glacier_area_frac = 0.0625 # 4/64 pixels in toy problem domain. 4/4 in Band 3  
            # open ground HRU is now gone:
            new_open_ground_area_frac = 0
            cells[cell_ids[0]][3].delete_hru(OPEN_GROUND_ID)
            # Confirm that there are (temporarily) no HRUs in this band
            assert cells[cell_ids[0]][3].num_hrus == 0
            # create new glacier HRU:
            cells[cell_ids[0]][3].create_hru(GLACIER_ID, new_glacier_area_frac, expected_root_zone_parms['22'])
            # Check that there is only the one glacier HRU in this band
            assert cells[cell_ids[0]][3].num_hrus == 1
            assert cells[cell_ids[0]][3].hrus[22].area_frac == new_glacier_area_frac
            assert cells[cell_ids[0]][3].hrus[22].root_zone_parms == expected_root_zone_parms['22']

        def test_new_glacier_growth_into_new_higher_band():
            """test_cells_dynamic -- Test #3: Simulates glacier growth to create a new elevation Band 4 (stealing one pixel from Band 3)"""
            new_glacier_area_frac = 0.015625 # 1/64 pixels in domain. 1/1 in Band 4
            # For consistency over whole domain, adjust Band 3 to compensate (this is normally taken care of by update of band_areas):
            cells[cell_ids[0]][3].hrus[22].area_frac -= 0.015625 # area_frac should now be 0.0625 - 0.015625 = 0.046875
            # Confirm existing number of Bands is 4
            assert len(cells[cell_ids[0]]) == 4
            # New Band's initial (single toy pixel) median elevation:
            pixel_elev = 2450
            # Create new Band
            Cell.create_band(cells[cell_ids[0]], pixel_elev)
            # Check that number of Bands has grown by one, and has no HRUs (yet)
            assert len(cells[cell_ids[0]]) == 5
            assert cells[cell_ids[0]][4].num_hrus == 0
            # Create the corresponding new glacier HRU
            cells[cell_ids[0]][4].create_hru(GLACIER_ID, new_glacier_area_frac, expected_root_zone_parms['22'])
            # Confirm that this new HRU was correctly instantiated
            assert cells[cell_ids[0]][4].num_hrus == 1
            assert cells[cell_ids[0]][4].hrus[22].area_frac == new_glacier_area_frac
            assert cells[cell_ids[0]][4].hrus[22].root_zone_parms == expected_root_zone_parms['22']
            # Confirm this Band's total area_frac is equal to that of its one HRU, and related quantities
            assert cells[cell_ids[0]][4].area_frac == new_glacier_area_frac
            assert cells[cell_ids[0]][4].area_frac_glacier == new_glacier_area_frac
            assert cells[cell_ids[0]][4].area_frac_non_glacier == 0
            assert cells[cell_ids[0]][4].area_frac_open_ground == 0

        def test_attempt_new_glacier_growth_into_unavailable_higher_band():
            """test_cells_dynamic -- Test #4: Simulates a (failing) attempt to grow the glacier into a new elevation Band 5 (no 0 pad available)"""
            pixel_elev = 2550
            with pytest.raises(IndexError):
                Cell.create_band(cells[cell_ids[0]], pixel_elev)
            # Confirm the number of bands has not changed
            assert len(cells[cell_ids[0]]) == 5

        def test_existing_glacier_shrink_out_of_band():
            """test_cells_dynamic -- Test #4: Simulates glacier recession completely out of elevation Band 4 (i.e. delete the Band)"""
            new_glacier_area_frac = 0
            Cell.delete_band(cells[cell_ids[0]], 4)
            # Confirm that there are 4 Bands in total for this cell
            assert len(cells[cell_ids[0]]) == 4
            # For consistency over whole domain, adjust Band 3 to compensate (this is normally taken care of by update of band_areas):
            cells[cell_ids[0]][3].hrus[22].area_frac += 0.015625
            # Confirm that all Band area fractions for this cell still sum to 1
            assert sum(cells[cell_ids[0]][band_idx].area_frac for band_idx, band in enumerate(cells[cell_ids[0]])) == 1

        def test_attempt_to_modify_nonexistent_band_hru():
            """test_cells_dynamic -- Test #5: Simulates a (failing) attempt to modify an HRU in a non-existent band is gracefully rejected"""
            # Check to confirm that no Band 0 currently exists
            assert cells[cell_ids[1]].left_padding == 1
            assert cells[cell_ids[1]][0] == None
            # Check that attempting to modify an HRU in this non-existent band fails
            with pytest.raises(Exception):
                cells[cell_ids[1]][0].median_elev = 9999

        def test_existing_glacier_shrink_revealing_new_lower_band():
            """test_cells_dynamic -- Test #6: Simulates glacier recession from the lowest existing band, to reveal a yet
            lower elevation band (consisting of a single pixel).  This is done in the second test cell, ID '23456' """
            # New band 0:
            pixel_elev = 1855
            Cell.create_band(cells[cell_ids[1]], pixel_elev)
            # Confirm that the new band was correctly placed in the first position for this cell
            assert cells[cell_ids[1]].left_padding == 0
            assert cells[cell_ids[1]].right_padding == 1
            # Confirm that there are now 4 valid Bands for this cell
            assert len(cells[cell_ids[1]]) == 4
            # Create an open ground HRU in this new lowest band
            new_open_ground_area_frac = 777 # NOTE: this is not a realistic number; just for testing
            cells[cell_ids[1]][0].create_hru(OPEN_GROUND_ID, new_open_ground_area_frac, expected_root_zone_parms['19'])
            assert cells[cell_ids[1]][0].num_hrus == 1
            assert cells[cell_ids[1]][0].area_frac == 777

        def test_attempt_new_glacier_growth_into_unavailable_lower_band():
            """test_cells_dynamic -- Test #7: Simulates the glacier expanding downward into an elevation band
            that has not been anticipated, i.e. not enough 0 pads were provided on the lower end in the snow band file"""
            pixel_elev = 1777
            with pytest.raises(IndexError):
                Cell.create_band(cells[cell_ids[1]], pixel_elev)
            # Confirm the number of bands and padding have not changed
            assert len(cells[cell_ids[0]]) == 4
            assert cells[cell_ids[1]].left_padding == 0
            assert cells[cell_ids[1]].right_padding == 1

        def test_glacier_growth_to_conceal_lowest_band():
            """test_cells_dynamic -- Test #8: Simulates the glacier re-covering the lowest band thickly enough 
            such that the pixels elevations in that area no longer belong to that band (i.e. the band must be deleted).
            NOTE: the glacier area fraction for existing Band 1 is not being updated in this test"""
            Cell.delete_band(cells[cell_ids[1]], 0)
            # Confirm that there are now 3 valid Bands for this cell (again)
            assert len(cells[cell_ids[1]]) == 3
            # Confirm update of padding
            assert cells[cell_ids[1]].left_padding == 1
            assert cells[cell_ids[1]].right_padding == 1

        def test_attempt_to_delete_band_from_middle():
            """test_cells_dynamic -- Test #9: Attempts to delete a band from the middle of the valid bands, which is not allowed """
            with pytest.raises(ValueError):
                Cell.delete_band(cells[cell_ids[1]], 2)

@pytest.mark.incremental
class TestsAreaFracUpdate:  # THIS IS TODO NEXT (Tuesday, June 16)
    def test_update_area_fracs(self, toy_domain_64px_cells):
        cells, cell_ids, num_snow_bands, band_size, expected_band_ids, expected_root_zone_parms = toy_domain_64px_cells
        pass

    def test_glacier_growth_over_open_ground_and_vegetation_in_band(self):
        """ Simulates Band 1 losing all its open ground and some vegetated area to glacier growth"""
        pass

    def test_glacier_growth_over_remaining_vegetation_in_band(self):
        """ Simulates Band 1 losing (some of) its only remaining non-glacier (vegetated) HRU to glacier growth"""
        pass
