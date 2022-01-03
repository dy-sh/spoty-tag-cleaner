from spoty.utils import SpotyContext
import spoty.audio_files
import click


@click.group("tag-cleaner")
def tag_cleaner():
    """
Plugin for cleaning tags in audio files.
    """
    pass


@tag_cleaner.command()
@click.option('--audio', '--a', multiple=True,
              help='Get audio files located at the specified local path. You can specify the audio file name as well.')
@click.option('--no-recursive', '-r', is_flag=True,
              help='Do not search in subdirectories from the specified path.')
@click.pass_context
def clean(
        ctx,
        audio,
        no_recursive
):
    """
Clean tags in audio files found in specified path.
    """

    all_tags_list = []

    # get csv

    audio_files = []
    tags_list_from_audio = []

    # get audio

    if len(audio) > 0:
        audio_paths = []
        for path in audio:
            if spoty.audio_files.is_audio_file(path):
                if spoty.utils.is_valid_file(path):
                    audio_files.append(path)
            elif spoty.utils.is_valid_path(path):
                audio_paths.append(path)
            else:
                click.echo(f'Cant find path or file: "{path}"', err=True)
                exit()

        file_names = spoty.audio_files.find_audio_files_in_paths(audio_paths, not no_recursive)
        audio_files.extend(file_names)

        tags_list = spoty.audio_files.read_audio_files_tags(audio_files, True, False)
        tags_list = spoty.utils.add_playlist_index_from_playlist_names(tags_list)
        tags_list_from_audio.extend(tags_list)
        all_tags_list.extend(tags_list)

    # replace ',' to ';' in ARTIST tag

    if len(all_tags_list) == 0:
        click.echo("No files found.")
        exit()

    replace_list = []
    for tags in all_tags_list:
        if 'ARTIST' in tags:
            if ',' in tags['ARTIST']:
                replace_list.append(tags)
    if len(replace_list) > 0:
        click.echo()
        click.echo('--------------------------------------------------------------')
        for tags in replace_list:
            file_name = tags['SPOTY_FILE_NAME']
            click.echo(f'ARTIST: "{tags["ARTIST"]}" in "{file_name}"')
        if click.confirm(f'Do you want to replace "," to ";" in ARTIST tag in this {len(replace_list)} audio files?'):
            for tags in replace_list:
                file_name = tags['SPOTY_FILE_NAME']
                new_tags = {}
                new_tags['ARTIST'] = tags['ARTIST'].replace(',', ';')
                spoty.audio_files.write_audio_file_tags(file_name, new_tags)
                tags['ARTIST'] = new_tags['ARTIST']

    # clean ISRC

    replace_list = []
    for tags in all_tags_list:
        if 'ISRC' in tags and tags['ISRC'] != fix_isrc(tags['ISRC']):
            replace_list.append(tags)
    if len(replace_list) > 0:
        click.echo()
        click.echo('--------------------------------------------------------------')
        for tags in replace_list:
            file_name = tags['SPOTY_FILE_NAME']
            click.echo(f'ISRC: "{tags["ISRC"]}" will become: "{fix_isrc(tags["ISRC"])}" in "{file_name}"')
        if (click.confirm(            f'Do you want to fix ISRC tag in {len(replace_list)} audio files?')):
            for tags in replace_list:
                file_name = tags['SPOTY_FILE_NAME']
                new_tags = {}
                new_tags['ISRC'] = fix_isrc(tags['ISRC'])
                spoty.audio_files.write_audio_file_tags(file_name, new_tags)
                tags['ISRC'] = fix_isrc(tags['ISRC'])


    # missing DEEZER_TRACK_ID but SOURCEID exist

    replace_list = []
    for tags in all_tags_list:
        if 'SOURCEID' in tags and 'DEEZER_TRACK_ID' not in tags \
                and 'SOURCE' in tags and tags['SOURCE'].upper() == "DEEZER":
            replace_list.append(tags)
    if len(replace_list) > 0:
        click.echo()
        click.echo('--------------------------------------------------------------')
        for tags in replace_list:
            file_name = tags['SPOTY_FILE_NAME']
            click.echo(f'SOURCEID: "{tags["SOURCEID"]}" in "{file_name}"')
        if click.confirm(f'Do you want to add DEEZER_TRACK_ID tag in this {len(replace_list)} audio files?'):
            for tags in replace_list:
                file_name = tags['SPOTY_FILE_NAME']
                new_tags = {}
                new_tags['DEEZER_TRACK_ID'] = tags['SOURCEID']
                spoty.audio_files.write_audio_file_tags(file_name, new_tags)
                tags['DEEZER_TRACK_ID'] = new_tags['DEEZER_TRACK_ID']

    replace_list = []
    for tags in all_tags_list:
        if 'SOURCEID' not in tags and 'DEEZER_TRACK_ID' not in tags \
                and 'SOURCE' in tags and tags['SOURCE'].upper() == "DEEZER":
            replace_list.append(tags)
    if len(replace_list) > 0:
        click.echo()
        click.echo('--------------------------------------------------------------')
        for tags in replace_list:
            file_name = tags['SPOTY_FILE_NAME']
            click.echo(f'"{file_name}"')
        click.confirm(
            f'This {len(replace_list)} audio files have SOURCE=="DEEZER" but have no SOURCEID and DEEZER_TRACK_ID. You can fix using "spoty get --d me get --a [LOCAL_PATH] duplicates add-missing-tags" command.')

    # missing SOURCE

    replace_list = []
    for tags in all_tags_list:
        if 'SOURCE' not in tags or tags['SOURCE'] == "":
            replace_list.append(tags)
    if len(replace_list) > 0:
        click.echo()
        click.echo('--------------------------------------------------------------')
        for tags in replace_list:
            file_name = tags['SPOTY_FILE_NAME']
            click.echo(f'"{file_name}"')
        click.confirm(
            f'This {len(replace_list)} audio files have no SOURCE tag. Fix it manually.')



def fix_isrc(isrc):
    return isrc.upper().replace('-','')