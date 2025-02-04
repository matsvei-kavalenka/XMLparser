import json as json_module
from argparse import ArgumentParser
from typing import List, Optional, Sequence
import requests
import xml.etree.ElementTree as element_tree


class UnhandledException(Exception):
    pass


def rss_parser(xml: str, limit: Optional[int] = None, json: bool = False) -> List[str]:
    """
    RSS parser.

    Args:
        xml: XML document as a string.
        limit: Number of the news to return. if None, returns all news.
        json: If True, format output as JSON.

    Returns:
        List of strings.
        Which then can be printed to stdout or written to file as a separate lines.

    Examples:
        xml = '<rss><channel><title>Some RSS Channel</title><link>https://some.rss.com</link><description>Some RSS Channel</description></channel></rss>'
        rss_parser(xml)
        ["Feed: Some RSS Channel",
        "Link: https://some.rss.com"]
        print("\\n".join(rss_parser(xmls)))
        Feed: Some RSS Channel
        Link: https://some.rss.com
    """
    if limit is not None and limit < 0:
        raise UnhandledException()

    channel_elements_dict = {"title": "Feed", "link": "Link", "lastBuildDate": "Last Build Date", "pubDate": "Publish Date", "language": "Language", "category": "Categories",
                             "managinEditor": "Editor", "description": "Description"}
    item_elements_dict = {"title": "Title", "author": "Author", "pubDate": "Published", "link": "Link", "category": "Categories", "description": ""}
    parsed_xml = element_tree.fromstring(xml)
    output = []
    if json:
        output.append(get_json_output(channel_elements_dict, item_elements_dict, parsed_xml, limit))
    else:
        output = get_output(channel_elements_dict, item_elements_dict, parsed_xml, limit)
    return output


def get_output(channel_elements_dict: dict, item_elements_dict: dict, parsed_xml, limit) -> List[str]:
    channels = parsed_xml.findall("channel")
    output = []
    for channel in channels:
        output.extend(get_channel_items(channel_elements_dict, channel))

        output[-1] = output[-1] + "\n"
        items = channel.findall("item")
        count = 0
        for item in items:
            if limit is not None and count >= limit:
                break
            for el in item_elements_dict.keys():
                if item.find(el) is not None:
                    content = item.find(el).text
                    if el == "category":
                        categories = [category.text for category in item.findall("category")]
                        if categories:
                            output.append(f"{channel_elements_dict[el]} {', '.join(categories)}")

                    elif el == "<description>":
                        output.append(f"\n{content}")
                    else:
                        output.append(f"{item_elements_dict[el]}: {content}")
            count += 1
    return output


def get_json_output(channel_elements_dict: dict, item_elements_dict: dict, parsed_xml, limit) -> str:
    channels = parsed_xml.findall("channel")
    output = {}

    for channel in channels:
        output.update(get_channel_items_json(channel_elements_dict, channel))

        items = channel.findall("item")
        count = 0
        items_list = []
        for item in items:
            if limit is not None and count >= limit:
                break
            items_dict = {}

            for el in item_elements_dict.keys():
                if item.find(el) is not None:
                    if el == "category":
                        categories = [category.text for category in item.findall("category")]
                        if categories:
                            items_dict[channel_elements_dict[el]] = categories
                    else:
                        content = item.find(el).text
                        items_dict[el] = content
            items_list.append(items_dict)
            count += 1
        if items_list:
            output["items"] = items_list
    json_formatted_str = json_module.dumps(output, indent=2)
    return json_formatted_str


def get_channel_items(channel_elements_dict, channel) -> List[str]:
    result = []
    for el in channel_elements_dict.keys():
        if channel.find(el) is not None:
            if el == "category":
                categories = [category.text for category in channel.findall("category")]
                if categories:
                    result.append(f"{channel_elements_dict[el]}: {categories}")
            else:
                result.append(f"{channel_elements_dict[el]}: {channel.find(el).text}")
    return result


def get_channel_items_json(channel_elements_dict, channel) -> dict:
    result = {}
    for el in channel_elements_dict.keys():
        if channel.find(el) is not None:
            if el == "category":
                categories = [category.text for category in channel.findall("category")]
                if categories:
                    result[channel_elements_dict[el]] = categories
            else:
                result[el] = channel.find(el).text
    return result


def main(argv: Optional[Sequence] = None):
    parser = ArgumentParser(
        prog="rss_reader",
        description="Pure Python command-line RSS reader.",
    )
    parser.add_argument("source", help="RSS URL", type=str, nargs="?")
    parser.add_argument(
        "--json", help="Print result as JSON in stdout", action="store_true"
    )
    parser.add_argument(
        "--limit", help="Limit news topics if this parameter provided", type=int
    )
    args = parser.parse_args(argv)
    args.source = "https://news.yahoo.com/rss"
    # args.json = True  # test value
    xml = requests.get(args.source).text
    try:
        print("\n".join(rss_parser(xml, args.limit, args.json)))
        return 0
    except Exception as e:
        raise UnhandledException(e)


if __name__ == "__main__":
    main()


